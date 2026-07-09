"""
RAG Retriever for Reality Lab Chatbot
Loads vector database and performs similarity search
"""

import json
import pickle
import faiss
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any


class RAGRetriever:
    def __init__(self, vector_db_dir: str):
        """
        Initialize RAG Retriever

        Args:
            vector_db_dir: Directory containing vector database files
        """
        self.db_dir = Path(vector_db_dir)
        self.model = None
        self.index = None
        self.documents = []
        self.config = {}

    def load(self):
        """Load vector database and embedding model"""
        print(f"Loading RAG system from: {self.db_dir}")

        # Load config
        config_file = self.db_dir / "config.json"
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        print(f"  Config loaded: {self.config['num_documents']} documents, {self.config['embedding_dim']}D embeddings")

        # Load embedding model
        print(f"  Loading embedding model: {self.config['model_name']}")
        self.model = SentenceTransformer(self.config['model_name'])

        # Load FAISS index
        index_file = self.db_dir / "faiss_index.bin"
        self.index = faiss.read_index(str(index_file))
        print(f"  FAISS index loaded: {self.index.ntotal} vectors")

        # Load documents
        docs_file = self.db_dir / "documents.pkl"
        with open(docs_file, 'rb') as f:
            self.documents = pickle.load(f)
        print(f"  Documents loaded: {len(self.documents)} items")

        print("✅ RAG system ready!")

    def search(self, query: str, k: int = 3, min_score: float = 0.3) -> List[Dict[str, Any]]:
        """
        Search for relevant documents

        Args:
            query: Search query
            k: Number of results to return
            min_score: Minimum similarity score (0-1)

        Returns:
            List of dictionaries with 'content', 'metadata', and 'score'
        """
        # Encode query
        query_embedding = self.model.encode([query], normalize_embeddings=True)

        # Search
        distances, indices = self.index.search(query_embedding.astype('float32'), k)

        # Filter and format results
        results = []
        for idx, score in zip(indices[0], distances[0]):
            if score >= min_score:
                doc = self.documents[idx]
                results.append({
                    "content": doc["content"],
                    "metadata": doc["metadata"],
                    "score": float(score)
                })

        return results

    def format_context(self, search_results: List[Dict[str, Any]], language: str = 'ko') -> str:
        """
        Format search results into context string for AI

        Args:
            search_results: List of search results
            language: 'ko' or 'en'

        Returns:
            Formatted context string
        """
        if not search_results:
            return ""

        if language == 'ko':
            context = "=== 데이터베이스 정보 ===\n\n"
        else:
            context = "=== Database Information ===\n\n"

        for i, result in enumerate(search_results, 1):
            context += f"{result['content']}\n---\n"

        return context.strip()


def test_retriever():
    """Test the RAG retriever"""
    retriever = RAGRetriever(str(Path(__file__).resolve().parent / "vector_db"))
    retriever.load()

    # Test queries
    test_queries = [
        ("연구실 위치가 어디인가요?", "ko"),
        ("김희원 교수님 이메일이 뭐예요?", "ko"),
        ("CVPR 2025 논문 제목은?", "ko"),
        ("Who are the MS students?", "en"),
    ]

    for query, lang in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")

        results = retriever.search(query, k=2)
        context = retriever.format_context(results, language=lang)

        print(context)


if __name__ == "__main__":
    test_retriever()
