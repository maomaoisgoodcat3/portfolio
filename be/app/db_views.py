PUBLIC_CHUNKS_VIEW_SQL = """
CREATE OR REPLACE VIEW public_chunks AS
SELECT
    chunks.id,
    chunks.text,
    chunks.embedding,
    documents.title,
    documents.public_url,
    documents.access,
    documents.lang
FROM chunks
JOIN documents ON documents.id = chunks.document_id
"""
