# =============================================================================
# Clinical Guideline Research Assistant
# Copyright (c) 2024. MIT License. See LICENSE file for details.
# =============================================================================
"""Lightweight search implementations using FREE tools.

- ChromaDB for vector search (replaces Milvus)
- Whoosh for text search (replaces Elasticsearch)
"""
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from whoosh import index
from whoosh.fields import Schema, TEXT, ID, NUMERIC
from whoosh.qparser import MultifieldParser
from whoosh.analysis import StemmingAnalyzer

from config.settings_lite import settings


class LiteVectorSearch:
    """Vector search using ChromaDB (FREE, no Docker required)."""
    
    def __init__(self, collection_name: str = "clinical_documents"):
        settings.ensure_directories()
        
        # Initialize ChromaDB with persistence
        self.client = chromadb.PersistentClient(
            path=str(settings.chroma_dir),
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        # Embedding model (runs locally, FREE)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def add_documents(
        self,
        doc_ids: List[str],
        texts: List[str],
        metadatas: Optional[List[Dict]] = None
    ):
        """Add documents to the vector store."""
        # Generate embeddings
        embeddings = self.embedding_model.encode(texts).tolist()
        
        self.collection.add(
            ids=doc_ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas or [{} for _ in doc_ids]
        )
    
    def search(
        self,
        query: str,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query]).tolist()
        
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        formatted = []
        if results['ids'] and results['ids'][0]:
            for i, doc_id in enumerate(results['ids'][0]):
                formatted.append({
                    "doc_id": doc_id,
                    "text": results['documents'][0][i] if results['documents'] else "",
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                    "score": 1 - results['distances'][0][i],  # Convert distance to similarity
                    "retrieval_method": "vector"
                })
        
        return formatted
    
    def count(self) -> int:
        """Get total document count."""
        return self.collection.count()


class LiteTextSearch:
    """Full-text search using Whoosh (FREE, pure Python)."""
    
    # Schema for clinical documents
    SCHEMA = Schema(
        doc_id=ID(stored=True, unique=True),
        title=TEXT(stored=True, analyzer=StemmingAnalyzer()),
        abstract=TEXT(stored=True, analyzer=StemmingAnalyzer()),
        full_text=TEXT(analyzer=StemmingAnalyzer()),
        authors=TEXT(stored=True),
        source_type=ID(stored=True),
        quality_score=NUMERIC(stored=True, numtype=float)
    )
    
    def __init__(self):
        settings.ensure_directories()
        self.index_dir = settings.whoosh_dir
        
        # Create or open index
        if index.exists_in(str(self.index_dir)):
            self.ix = index.open_dir(str(self.index_dir))
        else:
            self.ix = index.create_in(str(self.index_dir), self.SCHEMA)
    
    def add_document(
        self,
        doc_id: str,
        title: str,
        abstract: str,
        full_text: str = "",
        authors: str = "",
        source_type: str = "article",
        quality_score: float = 0.5
    ):
        """Add a document to the index."""
        writer = self.ix.writer()
        writer.update_document(
            doc_id=doc_id,
            title=title,
            abstract=abstract,
            full_text=full_text,
            authors=authors,
            source_type=source_type,
            quality_score=quality_score
        )
        writer.commit()
    
    def add_documents_bulk(self, documents: List[Dict[str, Any]]):
        """Add multiple documents at once."""
        writer = self.ix.writer()
        for doc in documents:
            writer.update_document(
                doc_id=doc.get("doc_id", ""),
                title=doc.get("title", ""),
                abstract=doc.get("abstract", ""),
                full_text=doc.get("full_text", ""),
                authors=doc.get("authors", ""),
                source_type=doc.get("source_type", "article"),
                quality_score=doc.get("quality_score", 0.5)
            )
        writer.commit()
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        fields: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for documents matching the query."""
        if fields is None:
            fields = ["title", "abstract", "full_text"]
        
        with self.ix.searcher() as searcher:
            parser = MultifieldParser(fields, self.ix.schema)
            parsed_query = parser.parse(query)
            
            results = searcher.search(parsed_query, limit=top_k)
            
            formatted = []
            for hit in results:
                formatted.append({
                    "doc_id": hit["doc_id"],
                    "title": hit.get("title", ""),
                    "abstract": hit.get("abstract", ""),
                    "authors": hit.get("authors", ""),
                    "source_type": hit.get("source_type", ""),
                    "quality_score": hit.get("quality_score", 0.5),
                    "score": hit.score,
                    "retrieval_method": "bm25"
                })
            
            return formatted
    
    def count(self) -> int:
        """Get total document count."""
        return self.ix.doc_count()


class HybridSearch:
    """Combines vector and text search with reciprocal rank fusion."""
    
    def __init__(self):
        self.vector_search = LiteVectorSearch()
        self.text_search = LiteTextSearch()
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        alpha: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining BM25 and vector results.
        
        Args:
            query: Search query
            top_k: Number of results to return
            alpha: Weight for BM25 vs vector (0.5 = equal weight)
        """
        # Get results from both methods
        bm25_results = self.text_search.search(query, top_k=top_k * 2)
        vector_results = self.vector_search.search(query, top_k=top_k * 2)
        
        # Reciprocal Rank Fusion
        doc_scores = {}
        
        for rank, result in enumerate(bm25_results, start=1):
            doc_id = result["doc_id"]
            doc_scores[doc_id] = doc_scores.get(doc_id, {"data": result})
            doc_scores[doc_id]["bm25_score"] = 1.0 / (60 + rank)
        
        for rank, result in enumerate(vector_results, start=1):
            doc_id = result["doc_id"]
            if doc_id not in doc_scores:
                doc_scores[doc_id] = {"data": result}
            doc_scores[doc_id]["vector_score"] = 1.0 / (60 + rank)
        
        # Compute hybrid scores
        fused = []
        for doc_id, data in doc_scores.items():
            bm25 = data.get("bm25_score", 0)
            vector = data.get("vector_score", 0)
            hybrid_score = alpha * bm25 + (1 - alpha) * vector
            
            result = data["data"].copy()
            result["hybrid_score"] = hybrid_score
            result["bm25_score"] = bm25
            result["vector_score"] = vector
            fused.append(result)
        
        # Sort by hybrid score
        fused.sort(key=lambda x: x["hybrid_score"], reverse=True)
        
        return fused[:top_k]
    
    def add_document(
        self,
        doc_id: str,
        title: str,
        abstract: str,
        full_text: str = "",
        authors: str = "",
        source_type: str = "article",
        quality_score: float = 0.5
    ):
        """Add document to both indices."""
        # Add to text search
        self.text_search.add_document(
            doc_id=doc_id,
            title=title,
            abstract=abstract,
            full_text=full_text,
            authors=authors,
            source_type=source_type,
            quality_score=quality_score
        )
        
        # Add to vector search (combine title + abstract for embedding)
        text_for_embedding = f"{title} {abstract}"
        self.vector_search.add_documents(
            doc_ids=[doc_id],
            texts=[text_for_embedding],
            metadatas=[{
                "title": title,
                "authors": authors,
                "source_type": source_type,
                "quality_score": quality_score
            }]
        )
    
    def count(self) -> Dict[str, int]:
        """Get document counts from both indices."""
        return {
            "text_search": self.text_search.count(),
            "vector_search": self.vector_search.count()
        }
