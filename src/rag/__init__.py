"""RAG (Retrieval-Augmented Generation) module for BrandGuard."""

from .ingest import ingest_documents, load_corpus
from .retrieve import retrieve_chunks, get_chunk_by_id

__all__ = ["ingest_documents", "load_corpus", "retrieve_chunks", "get_chunk_by_id"]
