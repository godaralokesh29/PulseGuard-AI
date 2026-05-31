import logging
import os
import uuid
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings
from google import genai

from backend.config import get_settings
from backend.database.redis_cache import cache_response

os.environ["ANONYMIZED_TELEMETRY"] = "False"

logger = logging.getLogger(__name__)
settings = get_settings()


class VectorDatabase:
    """Production Vector DB using ChromaDB and OpenAI Embeddings with Redis Cache."""

    def __init__(self, persist_directory: str = None, embedding_model: str = None):
        """Initialize ChromaDB client."""
        if persist_directory is None:
            persist_directory = settings.vector_db_path
        if embedding_model is None:
            embedding_model = settings.embedding_model

        os.makedirs(persist_directory, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False),
        )

        self.gemini_client = genai.Client(api_key=settings.gemini_api_key)
        self.embedding_model = embedding_model

        self.collection_name = "incident_rcas"
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    # ------------------------------------------------------------------
    # Embeddings
    # ------------------------------------------------------------------

    async def get_embedding(self, text: str) -> List[float]:
        """Generate embedding using Gemini API."""
        try:
            response = await self.gemini_client.aio.models.embed_content(
                model=self.embedding_model,
                contents=text,
            )
            return response.embeddings[0].values
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    # ------------------------------------------------------------------
    # Collection management
    # ------------------------------------------------------------------

    async def create_collection(self, name: str, metadata: Optional[Dict[str, Any]] = None):
        """Get or create a ChromaDB collection."""
        meta = {"hnsw:space": "cosine"}
        if metadata:
            meta.update(metadata)
        collection = self.client.get_or_create_collection(name=name, metadata=meta)
        logger.info(f"Collection ready: {name}")
        return collection

    def list_collections(self) -> List[str]:
        """List all collection names (synchronous)."""
        return [c.name for c in self.client.list_collections()]

    async def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Return stats for a given collection."""
        try:
            collection = self.client.get_or_create_collection(name=collection_name)
            count = collection.count()
            return {
                "collection_name": collection_name,
                "document_count": count,
                "metadata": collection.metadata,
            }
        except Exception as e:
            logger.error(f"Error getting stats for {collection_name}: {e}")
            return {"collection_name": collection_name, "document_count": 0, "error": str(e)}

    # ------------------------------------------------------------------
    # RCA-specific helpers
    # ------------------------------------------------------------------

    async def upsert_rca(
        self,
        incident_id: str,
        title: str,
        summary_text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Upsert a Root Cause Analysis document into the default collection."""
        doc_id = f"rca_{incident_id}"
        meta = {
            "incident_id": incident_id,
            "title": title,
        }
        if metadata:
            for k, v in metadata.items():
                if isinstance(v, (str, int, float, bool)):
                    meta[k] = v
                elif isinstance(v, list):
                    meta[k] = ", ".join(str(i) for i in v)

        embedding = await self.get_embedding(summary_text)
        self.collection.upsert(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[summary_text],
            metadatas=[meta],
        )
        logger.info(f"Upserted RCA {incident_id} as {doc_id}")
        return doc_id

    @cache_response(ttl_seconds=300)
    async def search_rcas(
        self,
        query: str,
        k: int = 5,
        error_type_filter: Optional[str] = None,
        tenant_filter: Optional[str] = None,
        min_confidence: float = 0.2,
    ) -> List[Dict[str, Any]]:
        """Search RCA documents with optional filters."""
        query_embedding = await self.get_embedding(query)

        where_filter = None
        conditions = []
        if error_type_filter:
            conditions.append({"error_type": error_type_filter})
        if tenant_filter:
            conditions.append({"affected_tenant": tenant_filter})
        if len(conditions) == 1:
            where_filter = conditions[0]
        elif len(conditions) > 1:
            where_filter = {"$and": conditions}

        query_kwargs: Dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": k,
            "include": ["documents", "metadatas", "distances"],
        }
        if where_filter:
            query_kwargs["where"] = where_filter

        results = self.collection.query(**query_kwargs)

        matches: List[Dict[str, Any]] = []
        if results["ids"] and len(results["ids"][0]) > 0:
            for i in range(len(results["ids"][0])):
                meta = results["metadatas"][0][i] or {}
                dist = results["distances"][0][i] if "distances" in results else 0
                similarity = max(0.0, 1.0 - dist)

                if similarity < min_confidence:
                    continue

                matches.append({
                    "vector_db_id": results["ids"][0][i],
                    "incident_id": meta.get("incident_id", "UNKNOWN"),
                    "title": meta.get("title", "Unknown Incident"),
                    "error_type": meta.get("error_type", "Unknown"),
                    "affected_tenant": meta.get("affected_tenant"),
                    "affected_service": meta.get("affected_service", "Unknown"),
                    "mitigation_metric": meta.get("mitigation_metric", "Unknown action"),
                    "mitigation_effectiveness": meta.get("mitigation_effectiveness", 0.0),
                    "resolution_confidence": meta.get("resolution_confidence", 50.0),
                    "similarity_score": similarity,
                    "content": results["documents"][0][i] if results.get("documents") else "",
                })

        return matches

    # ------------------------------------------------------------------
    # Generic document helpers
    # ------------------------------------------------------------------

    async def add_documents(
        self,
        documents=None,
        *,
        collection_name: Optional[str] = None,
        ids: Optional[List[str]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> List[str]:
        """Add documents to the vector DB.

        Supports two calling patterns:
          1) add_documents([{"id": ..., "content": ..., "metadata": {...}}, ...])
          2) add_documents(collection_name="x", documents=["text", ...],
                           ids=["id1", ...], metadatas=[{...}, ...])
        """
        if documents and isinstance(documents, list) and documents and isinstance(documents[0], dict):
            # Pattern 1: list-of-dicts
            if not documents:
                return []
            doc_ids = []
            texts = []
            metas = []
            for doc in documents:
                doc_id = str(doc.get("id", uuid.uuid4()))
                doc_ids.append(doc_id)
                texts.append(doc["content"])
                meta = {
                    k: v
                    for k, v in doc.get("metadata", {}).items()
                    if isinstance(v, (str, int, float, bool))
                }
                metas.append(meta)

            embeddings = [await self.get_embedding(t) for t in texts]
            self.collection.add(
                ids=doc_ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metas,
            )
            logger.info(f"Added {len(documents)} documents to default collection")
            return doc_ids

        # Pattern 2: keyword arguments (collection_name, documents, ids, metadatas)
        if collection_name is None:
            collection_name = self.collection_name

        target_collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        if documents is None:
            documents = []
        if not isinstance(documents, list):
            documents = [documents]
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]
        if metadatas is None:
            metadatas = [{} for _ in documents]

        if not documents:
            return []

        embeddings = [await self.get_embedding(t) for t in documents]
        target_collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        logger.info(f"Added {len(documents)} documents to collection '{collection_name}'")
        return ids

    async def search(
        self,
        collection_name: str,
        query: str,
        k: int = 5,
        where_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search a named collection by semantic similarity."""
        target_collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        if target_collection.count() == 0:
            return []

        query_embedding = await self.get_embedding(query)

        query_kwargs: Dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": min(k, target_collection.count()),
            "include": ["documents", "metadatas", "distances"],
        }
        if where_filter:
            query_kwargs["where"] = where_filter

        results = target_collection.query(**query_kwargs)

        matches: List[Dict[str, Any]] = []
        if results["ids"] and len(results["ids"][0]) > 0:
            for i in range(len(results["ids"][0])):
                dist = results["distances"][0][i] if "distances" in results else 0
                matches.append({
                    "id": results["ids"][0][i],
                    "document": results["documents"][0][i] if results.get("documents") else "",
                    "metadata": results["metadatas"][0][i] or {},
                    "relevance_score": max(0.0, 1.0 - dist),
                })
        return matches

    async def delete_document(self, collection_name: str, doc_id: str) -> bool:
        """Delete a document from a collection by ID."""
        try:
            target_collection = self.client.get_or_create_collection(name=collection_name)
            target_collection.delete(ids=[doc_id])
            logger.info(f"Deleted document {doc_id} from {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {e}")
            return False

    # ------------------------------------------------------------------
    # Metric-based search (kept from original)
    # ------------------------------------------------------------------

    @cache_response(ttl_seconds=300)
    async def search_by_metrics(
        self, error_type: str, spike_percentage: float, k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search similar incidents based on metrics. Cached in Redis."""
        query_text = f"Error Type: {error_type}. Anomaly Spike: {spike_percentage}%"
        query_embedding = await self.get_embedding(query_text)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )

        matches: List[Dict[str, Any]] = []
        if results["ids"] and len(results["ids"][0]) > 0:
            for i in range(len(results["ids"][0])):
                meta = results["metadatas"][0][i] or {}
                dist = results["distances"][0][i] if "distances" in results else 0
                similarity = max(0.0, 1.0 - dist)

                matches.append({
                    "vector_db_id": results["ids"][0][i],
                    "incident_id": meta.get("incident_id", "UNKNOWN"),
                    "title": meta.get("title", "Unknown Incident"),
                    "error_type": meta.get("error_type", "Unknown"),
                    "affected_tenant": meta.get("affected_tenant"),
                    "affected_service": meta.get("affected_service", "Unknown"),
                    "mitigation_metric": meta.get("mitigation_metric", "Unknown action"),
                    "mitigation_effectiveness": meta.get("mitigation_effectiveness", 0.0),
                    "resolution_confidence": meta.get("resolution_confidence", 50.0),
                    "similarity_score": similarity,
                    "content": results["documents"][0][i] if results.get("documents") else "",
                })

        return matches


# ------------------------------------------------------------------
# Singleton factory
# ------------------------------------------------------------------

_vector_db_instance = None


def get_vector_db() -> VectorDatabase:
    global _vector_db_instance
    if _vector_db_instance is None:
        _vector_db_instance = VectorDatabase()
    return _vector_db_instance
