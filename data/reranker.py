# =============================================================================
# Clinical Guideline Research Assistant
# Copyright (c) 2024. MIT License. See LICENSE file for details.
# =============================================================================
"""Reranker module using Cross-Encoder (FREE, runs locally).

Uses sentence-transformers cross-encoder for semantic reranking
of search results to improve retrieval quality.
"""
from typing import List, Dict, Any
from sentence_transformers import CrossEncoder


class Reranker:
    """Cross-encoder based reranker for search results."""
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """Initialize the reranker.
        
        Args:
            model_name: HuggingFace model name. Options:
                - "cross-encoder/ms-marco-MiniLM-L-6-v2" (fast, good quality)
                - "cross-encoder/ms-marco-MiniLM-L-12-v2" (slower, better)
        """
        self.model = CrossEncoder(model_name)
    
    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = 10,
        text_field: str = "abstract"
    ) -> List[Dict[str, Any]]:
        """Rerank documents based on relevance to query.
        
        Args:
            query: Search query
            documents: List of document dicts with text content
            top_k: Number of top results to return
            text_field: Field name containing document text
            
        Returns:
            Reranked list of documents with added 'rerank_score'
        """
        if not documents:
            return []
        
        # Prepare query-document pairs
        pairs = []
        for doc in documents:
            # Get text from document
            text = doc.get(text_field, "")
            if not text:
                text = doc.get("text", doc.get("title", ""))
            pairs.append([query, text[:512]])  # Limit text length
        
        # Get cross-encoder scores
        scores = self.model.predict(pairs)
        
        # Add scores to documents
        for i, doc in enumerate(documents):
            doc["rerank_score"] = float(scores[i])
        
        # Sort by rerank score (descending)
        reranked = sorted(documents, key=lambda x: x.get("rerank_score", 0), reverse=True)
        
        return reranked[:top_k]


# Singleton instance for efficiency
_reranker = None

def get_reranker() -> Reranker:
    """Get or create singleton reranker instance."""
    global _reranker
    if _reranker is None:
        _reranker = Reranker()
    return _reranker


def rerank_results(
    query: str,
    documents: List[Dict[str, Any]],
    top_k: int = 10
) -> List[Dict[str, Any]]:
    """Convenience function to rerank search results.
    
    Args:
        query: Search query
        documents: List of document dicts
        top_k: Number of results to return
        
    Returns:
        Reranked documents with rerank_score added
    """
    reranker = get_reranker()
    return reranker.rerank(query, documents, top_k)


if __name__ == "__main__":
    # Quick test
    print("Testing reranker...")
    
    test_docs = [
        {"doc_id": "1", "title": "Diabetes in elderly", "abstract": "Management of diabetes in older adults."},
        {"doc_id": "2", "title": "Hypertension guidelines", "abstract": "Blood pressure treatment recommendations."},
        {"doc_id": "3", "title": "Geriatric diabetes care", "abstract": "Specialized diabetes care for geriatric patients with comorbidities."}
    ]
    
    results = rerank_results("diabetes management elderly patients", test_docs)
    
    print("\nReranked results:")
    for r in results:
        print(f"  {r['doc_id']}: {r['title']} (score: {r['rerank_score']:.4f})")
