"""Retrieval functions for the RAG system."""

from __future__ import annotations

import os
from typing import Optional

import chromadb
from chromadb.utils import embedding_functions


def get_chroma_client() -> chromadb.ClientAPI:
    """Get the ChromaDB client."""
    persist_dir = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
    return chromadb.PersistentClient(path=persist_dir)


def get_embedding_function():
    """Get the default embedding function (uses sentence-transformers locally)."""
    return embedding_functions.DefaultEmbeddingFunction()


def retrieve_chunks(
    query: str,
    collection_name: str = "brand",
    top_k: int = 5,
) -> list[dict]:
    """Retrieve relevant chunks from the vector store.

    Args:
        query: The search query
        collection_name: Which collection to search ('brand' or 'product')
        top_k: Number of results to return

    Returns:
        List of chunk dicts with 'id', 'text', 'source' keys
    """
    try:
        client = get_chroma_client()
        embed_fn = get_embedding_function()

        # Get or create collection with embedding function
        collection = client.get_or_create_collection(
            name=collection_name,
            embedding_function=embed_fn,
            metadata={"hnsw:space": "cosine"},
        )

        # Check if collection is empty
        if collection.count() == 0:
            return _get_fallback_chunks(collection_name)

        # Search using query text (ChromaDB will embed it automatically)
        results = collection.query(
            query_texts=[query],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        # Format results
        chunks = []
        for i, doc_id in enumerate(results["ids"][0]):
            chunks.append(
                {
                    "id": doc_id,
                    "text": results["documents"][0][i],
                    "source": results["metadatas"][0][i].get("source", "unknown"),
                    "distance": results["distances"][0][i] if results.get("distances") else None,
                }
            )

        return chunks

    except Exception as e:
        print(f"Warning: Retrieval failed: {e}")
        return _get_fallback_chunks(collection_name)


def get_chunk_by_id(
    chunk_id: str,
    collection_name: Optional[str] = None,
) -> Optional[dict]:
    """Get a specific chunk by its ID.

    Args:
        chunk_id: The chunk ID to retrieve
        collection_name: Which collection to search (searches both if None)

    Returns:
        Chunk dict or None if not found
    """
    try:
        client = get_chroma_client()
        embed_fn = get_embedding_function()

        collections_to_search = [collection_name] if collection_name else ["brand", "product"]

        for coll_name in collections_to_search:
            try:
                collection = client.get_collection(coll_name, embedding_function=embed_fn)
                result = collection.get(ids=[chunk_id], include=["documents", "metadatas"])

                if result["documents"] and result["documents"][0]:
                    return {
                        "id": chunk_id,
                        "text": result["documents"][0],
                        "source": result["metadatas"][0].get("source", "unknown") if result["metadatas"] else "unknown",
                    }
            except Exception:
                continue

        return None

    except Exception as e:
        print(f"Warning: Get chunk by ID failed: {e}")
        return None


def get_chunks_by_ids(
    chunk_ids: list[str],
) -> dict[str, dict]:
    """Get multiple chunks by their IDs.

    Args:
        chunk_ids: List of chunk IDs to retrieve

    Returns:
        Dict mapping chunk_id -> chunk dict
    """
    chunks = {}
    for chunk_id in chunk_ids:
        chunk = get_chunk_by_id(chunk_id)
        if chunk:
            chunks[chunk_id] = chunk
    return chunks


def _get_fallback_chunks(collection_name: str) -> list[dict]:
    """Return fallback chunks when the vector store is empty or unavailable.

    This ensures the pipeline can still run for testing/demo purposes.
    """
    if collection_name == "brand":
        return [
            {
                "id": "fallback_brand_1",
                "text": """Our brand voice is confident yet approachable. We speak
                directly to our audience as peers, not as authorities lecturing
                from above. Use active voice, concrete examples, and avoid jargon
                unless our audience uses it daily.""",
                "source": "fallback",
            },
            {
                "id": "fallback_brand_2",
                "text": """When writing calls-to-action, be specific about the benefit.
                Don't say 'Learn more' - say 'See how teams cut review time by 50%'.
                Every CTA should answer the reader's question: 'What's in it for me?'""",
                "source": "fallback",
            },
        ]
    elif collection_name == "product":
        return [
            {
                "id": "fallback_product_1",
                "text": """Our platform helps teams collaborate more effectively.
                Key features include real-time editing, version control, and
                seamless integrations with existing workflows. Over 18,000 customers
                trust our platform for their identity management needs.""",
                "source": "fallback",
            },
            {
                "id": "fallback_product_2",
                "text": """Security features include SSO, MFA, and Universal Directory.
                Fortune 500 companies have seen 75% reduction in identity-related
                security incidents after implementing our platform.""",
                "source": "fallback",
            },
        ]
    else:
        return []


def compute_similarity(text1: str, text2: str) -> float:
    """Compute semantic similarity between two texts using embeddings.

    Args:
        text1: First text
        text2: Second text

    Returns:
        Cosine similarity score (0-1)
    """
    try:
        embed_fn = get_embedding_function()
        embeddings = embed_fn([text1, text2])

        # Compute cosine similarity
        import numpy as np
        emb1 = np.array(embeddings[0])
        emb2 = np.array(embeddings[1])

        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        return float(similarity)

    except Exception as e:
        print(f"Warning: Similarity computation failed: {e}")
        return 0.0


if __name__ == "__main__":
    # Test retrieval
    chunks = retrieve_chunks("brand voice guidelines", "brand")
    print(f"Retrieved {len(chunks)} chunks")
    for chunk in chunks:
        print(f"  - {chunk['id']}: {chunk['text'][:50]}...")
