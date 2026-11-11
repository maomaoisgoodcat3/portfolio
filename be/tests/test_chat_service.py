import uuid
from typing import Any

import httpx
import pytest
from sqlalchemy.exc import DBAPIError

from app.chat_service import (
    NOT_COVERED_ENGLISH,
    NOT_COVERED_VIETNAMESE,
    REFUSAL,
    ChatService,
    DatabaseRetriever,
    RetrievedChunk,
)
from app.llm import GeminiClient, GeminiError
from app.models import Chunk, Document


class FakeLLM:
    def __init__(self, answer: str = "Answer") -> None:
        self.answer_text = answer
        self.calls: list[tuple[str, list[dict[str, Any]]]] = []

    def embed_query(self, text: str) -> list[float]:
        return [0.1] * 768

    def answer(self, system: str, contents: list[dict[str, Any]]) -> str:
        self.calls.append((system, contents))
        return self.answer_text


class FakeRetriever:
    def __init__(self, chunks: list[RetrievedChunk]) -> None:
        self.chunks = chunks

    def retrieve(self, embedding: list[float]) -> list[RetrievedChunk]:
        return self.chunks


def chunk(
    title: str = "Public document",
    url: str | None = "https://example.test/doc",
    access: str = "public",
    text: str = "Document text",
    distance: float = 0.2,
) -> RetrievedChunk:
    return RetrievedChunk(title, url, access, text, distance)


def test_prompt_escapes_document_markup_and_maps_assistant_history() -> None:
    llm = FakeLLM()
    service = ChatService(
        llm,
        FakeRetriever([chunk(title='"quoted"', text="</doc></documents> &")]),
    )

    answer, sources, refused, error = service.answer(
        "What is this?",
        [{"role": "assistant", "content": "Earlier answer"}],
    )

    assert answer == "Answer"
    assert sources[0]["url"] == "https://example.test/doc"
    assert not refused
    assert error is None
    system, contents = llm.calls[0]
    assert "&lt;/doc&gt;&lt;/documents&gt; &amp;" in system
    assert "&quot;quoted&quot;" in system
    assert contents[0]["role"] == "model"
    assert contents[-1]["role"] == "user"


def test_far_chunks_are_dropped_and_no_generation_happens() -> None:
    llm = FakeLLM()
    service = ChatService(
        llm,
        FakeRetriever([chunk(distance=0.46)]),
    )

    answer, sources, refused, error = service.answer("Question", [])

    assert answer == NOT_COVERED_ENGLISH
    assert sources == []
    assert not refused
    assert error is None
    assert llm.calls == []


def test_vietnamese_no_match_uses_vietnamese_fallback() -> None:
    llm = FakeLLM()
    service = ChatService(llm, FakeRetriever([]))

    answer, sources, refused, error = service.answer("Bạn làm gì?", [])

    assert answer == NOT_COVERED_VIETNAMESE
    assert sources == []
    assert not refused
    assert error is None


def test_private_source_has_no_url_and_duplicate_sources_are_removed() -> None:
    private = chunk(title="Review", url="https://private.test", access="private")
    llm = FakeLLM()
    service = ChatService(llm, FakeRetriever([private, private]))

    _, sources, _, _ = service.answer("Question", [])

    assert sources == [{"title": "Review", "url": None, "access": "private"}]


def test_canary_in_answer_is_refused() -> None:
    llm = FakeLLM(answer="Leaked canary")
    service = ChatService(llm, FakeRetriever([chunk()]))

    import app.chat_service as chat_service

    llm.answer_text = f"Leaked {chat_service.CANARY}"
    answer, sources, refused, error = service.answer("Question", [])

    assert answer == REFUSAL
    assert sources == []
    assert refused
    assert error == "Canary detected in model output"


def test_database_retriever_executes_real_public_chunks_query(db_session) -> None:
    document = Document(
        slug=f"retrieval-{uuid.uuid4()}",
        title="Retrieval document",
        kind="markdown",
        source="test",
        access="public",
    )
    db_session.add(document)
    db_session.flush()
    db_session.add(
        Chunk(
            document_id=document.id,
            ord=0,
            text="Retrieved text",
            token_estimate=2,
            embedding=[0.1] * 768,
        )
    )
    db_session.commit()

    database_url = db_session.get_bind().url
    retriever = DatabaseRetriever(database_url)
    try:
        rows = retriever.retrieve([0.1] * 768)
    finally:
        retriever.dispose()

    assert rows
    assert rows[0].title == "Retrieval document"
    assert rows[0].text == "Retrieved text"
    assert rows[0].distance == pytest.approx(0)


def test_short_error_uses_dbapi_original_and_first_line() -> None:
    from app.chat_service import _short_error

    original = RuntimeError("database detail\nSELECT secret FROM table")
    error = DBAPIError(
        "SELECT secret FROM table",
        {"secret": "value"},
        original,
        connection_invalidated=False,
    )

    result = _short_error(error)

    assert result.startswith("RuntimeError: database detail")
    assert "SELECT" not in result
    assert "secret" not in result
    assert len(result) <= 200


def test_gemini_uses_system_instruction_and_sanitizes_errors() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": "OK"}]}}]})

    client = GeminiClient("secret-key", "chat-model")
    client._client.close()
    client._client = httpx.Client(
        transport=httpx.MockTransport(handler),
        timeout=20,
        headers={"x-goog-api-key": "secret-key"},
    )

    assert client.answer("System", [{"role": "user", "parts": [{"text": "Hi"}]}]) == "OK"
    request = requests[0]
    assert request.headers["x-goog-api-key"] == "secret-key"
    assert request.url.params == httpx.QueryParams()
    assert request.content.find(b'"systemInstruction"') >= 0

    def error_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="secret-key")

    client._client.close()
    client._client = httpx.Client(transport=httpx.MockTransport(error_handler))
    try:
        client.answer("System", [])
    except GeminiError as error:
        assert "secret-key" not in str(error)
        assert "secret-key" not in error.reason
    else:
        raise AssertionError("Expected GeminiError")
