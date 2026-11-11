import hashlib
import os
import subprocess
import sys
from pathlib import Path

import httpx
import pytest
from sqlalchemy import text

from app import ingest
from app.models import Chunk, Document


def _embedding_response(request: httpx.Request) -> httpx.Response:
    return httpx.Response(
        200,
        json={"embedding": {"values": [0.0] * 768}},
        request=request,
    )


def test_chunk_text_uses_500_token_chunks_and_overlap() -> None:
    source = "\n\n".join(f"paragraph {index} " + ("x" * 800) for index in range(8))

    chunks = ingest.chunk_text(source)

    assert len(chunks) > 1
    assert all(len(chunk) <= ingest.MAX_CHARS + ingest.OVERLAP_CHARS for chunk in chunks)
    assert chunks[1].startswith(chunks[0][-ingest.OVERLAP_CHARS :])


def test_ingest_import_does_not_require_application_settings() -> None:
    environment = os.environ.copy()
    for name in (
        "TOTP_ENC_KEY",
        "POSTGRES_HOST",
        "POSTGRES_PORT",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_DB",
    ):
        environment.pop(name, None)

    result = subprocess.run(
        [sys.executable, "-c", "import app.ingest"],
        capture_output=True,
        text=True,
        env=environment,
        check=False,
    )

    assert result.returncode == 0


def test_gdoc_redirect_is_not_followed() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            302,
            headers={"location": "https://accounts.google.com/"},
            request=request,
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))

    with pytest.raises(ingest.IngestError, match="not shared publicly"):
        ingest._fetch_document(
            {"kind": "gdoc", "source": "doc-id"},
            client,
            None,
        )


def test_local_source_must_stay_inside_content_directory(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    content_root = tmp_path / "content"
    (content_root / "pdf").mkdir(parents=True)
    monkeypatch.setattr(ingest, "CONTENT_ROOT", content_root)

    with pytest.raises(
        ingest.IngestError, match="source path outside content directory"
    ):
        ingest._fetch_document(
            {"kind": "markdown", "source": "../pdf/private.md"},
            httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200))),
            None,
        )


def test_github_token_is_only_sent_as_authorization_header() -> None:
    seen_headers: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen_headers.update({key.lower(): value for key, value in request.headers.items()})
        return httpx.Response(200, text="README", request=request)

    ingest._fetch_document(
        {"kind": "github_readme", "source": "owner/repo"},
        httpx.Client(transport=httpx.MockTransport(handler)),
        "secret-token",
    )

    assert seen_headers["authorization"] == "Bearer secret-token"
    assert "secret-token" not in str(seen_headers.get("user-agent", ""))


def test_private_entry_with_public_url_is_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config = tmp_path / "documents.yaml"
    config.write_text(
        "- slug: private\n"
        "  title: Private\n"
        "  kind: markdown\n"
        "  source: private.md\n"
        "  access: private\n"
        "  public_url: https://example.com\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(ingest, "CONFIG_PATH", config)

    with pytest.raises(ingest.IngestError, match="invalid documents.yaml"):
        ingest._load_entries()


def test_invalid_yaml_is_rejected_before_ingest(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config = tmp_path / "documents.yaml"
    config.write_text("not: a list\n", encoding="utf-8")
    monkeypatch.setattr(ingest, "CONFIG_PATH", config)
    called = False

    def fail_if_called(*args: object, **kwargs: object) -> bool:
        nonlocal called
        called = True
        return False

    monkeypatch.setattr(ingest, "ingest", fail_if_called)
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
    monkeypatch.setenv("GEMINI_API_KEY", "key")

    assert ingest.main() == 1
    assert called is False


def test_empty_markdown_fails_with_no_text_extracted(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    content_root = tmp_path / "content"
    markdown_dir = content_root / "md"
    markdown_dir.mkdir(parents=True)
    (markdown_dir / "empty.md").write_text(" \n\n\t", encoding="utf-8")
    monkeypatch.setattr(ingest, "CONTENT_ROOT", content_root)

    with pytest.raises(ingest.IngestError, match="no text extracted"):
        content = ingest._normalize(
            ingest._fetch_document(
                {"kind": "markdown", "source": "empty.md"},
                httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200))),
                None,
            )
        )
        if not content:
            raise ingest.IngestError("no text extracted")


def test_unchanged_hash_updates_metadata_without_embedding(
    db_session, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    content_root = tmp_path / "content"
    markdown_dir = content_root / "md"
    markdown_dir.mkdir(parents=True)
    content = "A stable document."
    (markdown_dir / "doc.md").write_text(content, encoding="utf-8")
    digest = hashlib.sha256(content.encode()).hexdigest()
    document = Document(
        slug="stable",
        title="Old title",
        kind="markdown",
        source="doc.md",
        public_url=None,
        access="private",
        content_hash=digest,
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    db_session.add(
        Chunk(
            document_id=document.id,
            ord=0,
            text=content,
            token_estimate=5,
            embedding=[0.0] * 768,
        )
    )
    db_session.commit()
    monkeypatch.setattr(ingest, "CONTENT_ROOT", content_root)

    def fail_embedding(request: httpx.Request) -> httpx.Response:
        raise AssertionError("embedding must be skipped")

    failed = ingest.ingest(
        db_session.get_bind().url.render_as_string(hide_password=False),
        [
            {
                "slug": "stable",
                "title": "New title",
                "kind": "markdown",
                "source": "doc.md",
                "public_url": "https://example.com/doc",
                "access": "public",
                "lang": "en",
            }
        ],
        "key",
        "gemini-embedding-001",
        None,
        httpx.Client(transport=httpx.MockTransport(fail_embedding)),
    )

    assert failed is False
    row = db_session.execute(
        text("SELECT title, access, public_url FROM documents WHERE slug = 'stable'")
    ).one()
    assert row == ("New title", "public", "https://example.com/doc")


def test_failure_keeps_old_chunks(
    db_session, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    content_root = tmp_path / "content"
    markdown_dir = content_root / "md"
    markdown_dir.mkdir(parents=True)
    (markdown_dir / "doc.md").write_text("Changed content.", encoding="utf-8")
    document = Document(
        slug="old",
        title="Old",
        kind="markdown",
        source="doc.md",
        content_hash="old-hash",
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    db_session.add(
        Chunk(
            document_id=document.id,
            ord=0,
            text="Old chunk",
            token_estimate=2,
            embedding=[0.0] * 768,
        )
    )
    db_session.commit()
    monkeypatch.setattr(ingest, "CONTENT_ROOT", content_root)
    monkeypatch.setattr(ingest.time, "sleep", lambda seconds: None)

    def failing_embedding(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, request=request)

    failed = ingest.ingest(
        db_session.get_bind().url.render_as_string(hide_password=False),
        [
            {
                "slug": "old",
                "title": "Old",
                "kind": "markdown",
                "source": "doc.md",
                "public_url": None,
                "access": "public",
                "lang": "en",
            }
        ],
        "key",
        "gemini-embedding-001",
        None,
        httpx.Client(transport=httpx.MockTransport(failing_embedding)),
    )

    assert failed is True
    row = db_session.execute(
        text(
            "SELECT content_hash, last_error FROM documents WHERE slug = 'old'"
        )
    ).one()
    assert row[0] == "old-hash"
    assert row[1] == "embedding request failed"
    assert db_session.query(Chunk).filter(Chunk.document_id == document.id).one().text == "Old chunk"


def test_new_document_failure_keeps_row_and_last_error(
    db_session, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys
) -> None:
    content_root = tmp_path / "content"
    (content_root / "md").mkdir(parents=True)
    monkeypatch.setattr(ingest, "CONTENT_ROOT", content_root)

    failed = ingest.ingest(
        db_session.get_bind().url.render_as_string(hide_password=False),
        [
            {
                "slug": "new-failure",
                "title": "New failure",
                "kind": "markdown",
                "source": "missing.md",
                "public_url": None,
                "access": "public",
                "lang": "en",
            }
        ],
        "key",
        "gemini-embedding-001",
        None,
    )

    assert failed is True
    row = db_session.execute(
        text(
            "SELECT content_hash, last_error FROM documents "
            "WHERE slug = 'new-failure'"
        )
    ).one()
    assert row == (None, "markdown fetch failed")
    assert "new-failure failed 0 markdown fetch failed" in capsys.readouterr().out
