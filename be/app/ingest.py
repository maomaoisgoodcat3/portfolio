import hashlib
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import httpx
import yaml
from pypdf import PdfReader
from sqlalchemy import bindparam, create_engine, text
from sqlalchemy.exc import ArgumentError
from sqlalchemy.pool import NullPool

from app.db_url import normalize_database_url

ROOT = Path(__file__).resolve().parents[2]
CONTENT_ROOT = ROOT / "content"
CONFIG_PATH = CONTENT_ROOT / "documents.yaml"
MAX_CHARS = 500 * 4
OVERLAP_CHARS = 60 * 4
GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
SAFE_ERROR = "document ingest failed"
EMBED_REQUEST_INTERVAL = 60 / 80


class IngestError(Exception):
    pass


def _normalize(text_value: str) -> str:
    paragraphs = [" ".join(part.split()) for part in text_value.split("\n\n")]
    return "\n\n".join(part for part in paragraphs if part)


def chunk_text(text_value: str) -> list[str]:
    paragraphs = [part for part in text_value.split("\n\n") if part]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        pieces = (
            [
                paragraph[index : index + MAX_CHARS]
                for index in range(0, len(paragraph), MAX_CHARS)
            ]
            if len(paragraph) > MAX_CHARS
            else [paragraph]
        )
        for piece in pieces:
            candidate = f"{current}\n\n{piece}" if current else piece
            if current and len(candidate) > MAX_CHARS:
                chunks.append(current)
                overlap = current[-OVERLAP_CHARS:]
                current = f"{overlap}\n\n{piece}"
            else:
                current = candidate
    if current:
        chunks.append(current)
    return chunks


def _safe_content_path(source: str, directory: Path) -> Path:
    candidate = (directory / source).resolve()
    try:
        candidate.relative_to(directory.resolve())
    except ValueError as error:
        raise IngestError("source path outside content directory") from error
    return candidate


def _fetch_document(
    entry: dict[str, Any],
    client: httpx.Client,
    github_token: str | None,
) -> str:
    kind = entry["kind"]
    source = entry["source"]
    if kind == "github_readme":
        headers = {"Accept": "application/vnd.github.raw"}
        if github_token:
            headers["Authorization"] = f"Bearer {github_token}"
        response = client.get(
            f"https://api.github.com/repos/{source}/readme",
            headers=headers,
        )
        if response.status_code != 200:
            raise IngestError("GitHub README fetch failed")
        return response.text
    if kind == "gdoc":
        response = client.get(
            f"https://docs.google.com/document/d/{source}/export?format=txt",
            follow_redirects=False,
        )
        content_type = response.headers.get("content-type", "").lower()
        if response.status_code != 200 or not content_type.startswith("text/plain"):
            raise IngestError("not shared publicly")
        return response.text
    if kind == "pdf":
        path = _safe_content_path(source, CONTENT_ROOT / "pdf")
        try:
            return "\n\n".join(
                page.extract_text() or "" for page in PdfReader(path).pages
            )
        except OSError as error:
            raise IngestError("PDF fetch failed") from error
    if kind == "markdown":
        path = _safe_content_path(source, CONTENT_ROOT / "md")
        try:
            return path.read_text(encoding="utf-8")
        except OSError as error:
            raise IngestError("markdown fetch failed") from error
    raise IngestError("invalid document kind")


def _embed(
    chunks: list[str],
    model: str,
    api_key: str,
    client: httpx.Client,
) -> list[list[float]]:
    vectors: list[list[float]] = []
    request_times: list[float] = []
    token_times: list[tuple[float, int]] = []
    for chunk in chunks:
        now = time.monotonic()
        request_times = [stamp for stamp in request_times if now - stamp < 60]
        token_times = [
            (stamp, tokens)
            for stamp, tokens in token_times
            if now - stamp < 60
        ]
        if request_times:
            time.sleep(max(0, EMBED_REQUEST_INTERVAL - (now - request_times[-1])))
        now = time.monotonic()
        if token_times and sum(tokens for _, tokens in token_times) + (
            (len(chunk) + 3) // 4
        ) >= 25_000:
            time.sleep(60 - (now - token_times[0][0]))
        payload = {
            "content": {"parts": [{"text": chunk}]},
            "taskType": "RETRIEVAL_DOCUMENT",
            "outputDimensionality": 768,
        }
        last_response: httpx.Response | None = None
        for attempt, delay in enumerate((0, 5, 15, 45)):
            if delay:
                time.sleep(delay)
            response = client.post(
                f"{GEMINI_BASE}/{model}:embedContent",
                headers={"x-goog-api-key": api_key},
                json=payload,
            )
            request_times.append(time.monotonic())
            token_times.append((time.monotonic(), (len(chunk) + 3) // 4))
            last_response = response
            if response.status_code not in (429,) and response.status_code < 500:
                break
            if attempt == 3:
                break
        if last_response is None or last_response.status_code != 200:
            raise IngestError("embedding request failed")
        try:
            values = last_response.json()["embedding"]["values"]
            vectors.append([float(value) for value in values])
        except (KeyError, TypeError, ValueError) as error:
            raise IngestError("embedding response invalid") from error
    return vectors


def _load_entries() -> list[dict[str, Any]]:
    try:
        loaded = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise IngestError("invalid documents.yaml") from error
    if loaded is None:
        return []
    if not isinstance(loaded, list):
        raise IngestError("invalid documents.yaml")
    entries: list[dict[str, Any]] = []
    for item in loaded:
        if not isinstance(item, dict):
            raise IngestError("invalid documents.yaml")
        required = ("slug", "title", "kind", "source")
        if any(
            not isinstance(item.get(key), str) or not item[key].strip()
            for key in required
        ):
            raise IngestError("invalid documents.yaml")
        access = item.get("access", "public")
        if access not in {"public", "private"} or item["kind"] not in {
            "github_readme",
            "gdoc",
            "pdf",
            "markdown",
        }:
            raise IngestError("invalid documents.yaml")
        public_url = item.get("public_url")
        if public_url is not None and not isinstance(public_url, str):
            raise IngestError("invalid documents.yaml")
        if access == "private" and "public_url" in item:
            raise IngestError("invalid documents.yaml")
        lang = item.get("lang", "en")
        if not isinstance(lang, str) or not lang.strip():
            raise IngestError("invalid documents.yaml")
        entries.append(
            {
                "slug": item["slug"],
                "title": item["title"],
                "kind": item["kind"],
                "source": item["source"],
                "public_url": public_url,
                "access": access,
                "lang": lang,
            }
        )
    return entries


def _safe_failure(error: Exception) -> str:
    if isinstance(error, IngestError):
        return str(error)
    return SAFE_ERROR


def ingest(
    database_url: str,
    entries: list[dict[str, Any]],
    api_key: str,
    model: str,
    github_token: str | None,
    client: httpx.Client | None = None,
) -> bool:
    engine = create_engine(
        normalize_database_url(database_url),
        poolclass=NullPool,
        hide_parameters=True,
    )
    http_client = client or httpx.Client(timeout=httpx.Timeout(10.0))
    failed = False
    seen_slugs = {entry["slug"] for entry in entries}
    try:
        for entry in entries:
            try:
                with engine.begin() as connection:
                    existing = connection.execute(
                        text(
                            """
                            INSERT INTO documents
                                (slug, title, kind, source, public_url, access, lang)
                            VALUES
                                (:slug, :title, :kind, :source, :public_url,
                                 :access, :lang)
                            ON CONFLICT (slug) DO UPDATE SET
                                title = EXCLUDED.title,
                                kind = EXCLUDED.kind,
                                source = EXCLUDED.source,
                                public_url = EXCLUDED.public_url,
                                access = EXCLUDED.access,
                                lang = EXCLUDED.lang,
                                last_error = NULL,
                                updated_at = now()
                            RETURNING id, content_hash
                            """
                        ),
                        entry,
                    ).mappings().one()
                content = _normalize(
                    _fetch_document(entry, http_client, github_token)
                )
                if not content:
                    raise IngestError("no text extracted")
                chunks = chunk_text(content)
                if not chunks:
                    raise IngestError("no text extracted")
                digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
                if existing and existing["content_hash"] == digest:
                    with engine.begin() as connection:
                        connection.execute(
                            text(
                                """
                                UPDATE documents
                                SET title = :title, kind = :kind, source = :source,
                                    public_url = :public_url, access = :access,
                                    lang = :lang, last_error = NULL, updated_at = now()
                                WHERE slug = :slug
                                """
                            ),
                            {**entry},
                        )
                    print(f"{entry['slug']} unchanged {len(chunks)}")
                    continue
                vectors = _embed(chunks, model, api_key, http_client)
                with engine.begin() as connection:
                    document_id = connection.execute(
                        text(
                            """
                            INSERT INTO documents
                                (slug, title, kind, source, public_url, access, lang,
                                 content_hash, ingested_at, last_error, updated_at)
                            VALUES
                                (:slug, :title, :kind, :source, :public_url, :access,
                                 :lang, :content_hash, now(), NULL, now())
                            ON CONFLICT (slug) DO UPDATE SET
                                title = EXCLUDED.title, kind = EXCLUDED.kind,
                                source = EXCLUDED.source, public_url = EXCLUDED.public_url,
                                access = EXCLUDED.access, lang = EXCLUDED.lang,
                                content_hash = EXCLUDED.content_hash,
                                ingested_at = EXCLUDED.ingested_at,
                                last_error = NULL, updated_at = now()
                            RETURNING id
                            """
                        ),
                        {**entry, "content_hash": digest},
                    ).scalar_one()
                    connection.execute(
                        text("DELETE FROM chunks WHERE document_id = :document_id"),
                        {"document_id": document_id},
                    )
                    connection.execute(
                        text(
                            """
                            INSERT INTO chunks
                                (document_id, ord, text, token_estimate, embedding)
                            VALUES (
                                :document_id, :ord, :text, :token_estimate,
                                CAST(:embedding AS vector)
                            )
                            """
                        ),
                        [
                            {
                                "document_id": document_id,
                                "ord": index,
                                "text": chunk,
                                "token_estimate": (len(chunk) + 3) // 4,
                                "embedding": "[" + ",".join(map(str, vector)) + "]",
                            }
                            for index, (chunk, vector) in enumerate(zip(chunks, vectors))
                        ],
                    )
                print(f"{entry['slug']} ingested {len(chunks)}")
            except Exception as error:
                failed = True
                with engine.begin() as connection:
                    connection.execute(
                        text(
                            "UPDATE documents SET last_error = :last_error, "
                            "updated_at = now() WHERE slug = :slug"
                        ),
                        {"last_error": _safe_failure(error), "slug": entry["slug"]},
                    )
                print(
                    f"{entry['slug']} failed 0 {_safe_failure(error)}"
                )
        if entries:
            with engine.begin() as connection:
                connection.execute(
                    text("DELETE FROM documents WHERE slug NOT IN :slugs").bindparams(
                        bindparam("slugs", expanding=True)
                    ),
                    {"slugs": list(seen_slugs)},
                )
        with engine.begin() as connection:
            connection.execute(
                text("DELETE FROM chat_logs WHERE created_at < :cutoff"),
                {"cutoff": datetime.now(timezone.utc) - timedelta(days=30)},
            )
    finally:
        if client is None:
            http_client.close()
        engine.dispose()
    return failed


def main() -> int:
    try:
        entries = _load_entries()
        database_url = os.getenv("DATABASE_URL", "").strip()
        if not database_url:
            raise IngestError("DATABASE_URL is missing or not valid")
        if not entries:
            print("warning: documents.yaml is empty; no documents deleted")
            return 0
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            raise IngestError("GEMINI_API_KEY is missing")
        failed = ingest(
            database_url,
            entries,
            api_key,
            os.getenv("GEMINI_EMBED_MODEL", "gemini-embedding-001"),
            os.getenv("GITHUB_TOKEN"),
        )
    except (IngestError, ArgumentError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
