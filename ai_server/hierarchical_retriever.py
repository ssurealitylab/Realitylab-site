#!/usr/bin/env python3
"""
Hierarchical RAG Retriever
2-stage retrieval: Category classification → Focused search
"""

import json
import pickle
import faiss
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional


class HierarchicalRetriever:
    def __init__(self, rag_dir: str):
        self.rag_dir = Path(rag_dir)
        self.model = None
        self.categories = {}
        self.category_indexes = {}
        self.category_docs = {}

        # Category keywords for classification
        self.category_keywords = {
            "members": ["교수", "professor", "prof", "김희원", "heewon", "지도교수", "책임자", "학생", "student", "연구원", "researcher", "석사", "master", "인턴", "intern", "멤버", "member", "연구생", "수", "몇 명", "명단", "구성원", "졸업생", "alumni", "졸업", "graduate", "former", "박사", "phd"],
            "news": ["뉴스", "news", "소식", "발표", "announcement", "accept", "award", "수상"],
            "publications": ["논문", "paper", "publication", "학회", "conference", "journal", "cvpr", "iccv", "wacv", "bmvc", "aaai", "eccv", "nips", "neurips", "icml", "2023", "2024", "2025", "2026", "최신", "recent", "latest", "higlassrm", "mbti", "dynscene"],
            "lab_info": ["연구실", "lab", "위치", "location", "주소", "address", "contact", "연락처", "이메일", "email", "전화", "phone"],
            "research": ["연구", "research", "분야", "area", "비전", "vision", "로봇", "robot", "컴퓨터비전", "딥러닝", "deep learning", "computer vision"],
            "qa": ["지원", "apply", "join", "입학", "admission", "어떻게", "how", "방법", "procedure", "프로젝트", "project", "기술", "스택", "도구", "tool", "있나요", "되나요", "되어있나요", "있어요", "되어있어요", "되는지", "되는가", "없나요"]
        }

    def load(self):
        """Load hierarchical RAG system"""
        print(f"Loading Hierarchical RAG from: {self.rag_dir}")

        # Load categories metadata
        metadata_file = self.rag_dir / "categories.json"
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        self.categories = metadata['categories']
        model_name = metadata['model_name']

        # Load embedding model
        print(f"  Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)

        # Load each category
        for category in self.categories:
            category_dir = self.rag_dir / category
            if not category_dir.exists():
                print(f"  Warning: {category} directory not found")
                continue

            # Load config
            config_file = category_dir / "config.json"
            with open(config_file, 'r') as f:
                config = json.load(f)

            # Load FAISS index
            index_file = category_dir / "faiss_index.bin"
            index = faiss.read_index(str(index_file))
            self.category_indexes[category] = index

            # Load documents
            docs_file = category_dir / "documents.pkl"
            with open(docs_file, 'rb') as f:
                docs = pickle.load(f)
            self.category_docs[category] = docs

            print(f"  ✅ {category}: {config['num_documents']} docs")

        print("✅ Hierarchical RAG ready!")

    def classify_query(self, query: str) -> List[str]:
        """
        Classify query to determine relevant categories
        Returns list of categories (most relevant first)
        """
        query_lower = query.lower()
        scores = {}

        for category, keywords in self.category_keywords.items():
            score = sum(1 for kw in keywords if kw in query_lower)
            if score > 0:
                scores[category] = score

        # Sort by score
        sorted_categories = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        # Return categories with scores > 0
        result = [cat for cat, score in sorted_categories if score > 0]

        # If no match, search all categories
        if not result:
            result = list(self.categories)

        return result

    def search_category(self, category: str, query: str, k: int = 5, min_score: float = 0.15) -> List[Dict[str, Any]]:
        """Search within a specific category"""
        if category not in self.category_indexes:
            return []

        # Encode query
        query_embedding = self.model.encode([query], normalize_embeddings=True)

        # Search
        index = self.category_indexes[category]
        distances, indices = index.search(query_embedding.astype('float32'), k)

        # Filter and format results
        results = []
        for idx, score in zip(indices[0], distances[0]):
            if score >= min_score:
                doc = self.category_docs[category][idx]
                results.append({
                    "content": doc["content"],
                    "metadata": doc["metadata"],
                    "score": float(score),
                    "category": category
                })

        return results

    def search(self, query: str, k: int = 5, min_score: float = 0.15, max_categories: int = 3) -> List[Dict[str, Any]]:
        """
        2-stage hierarchical search:
        1. Classify query to find relevant categories
        2. Search within those categories
        3. Add keyword-based results for recency queries
        """
        # Stage 1: Classify
        relevant_categories = self.classify_query(query)[:max_categories]

        # Always include 'qa' (researcher-verified Q&A) - it's small and high-value
        if 'qa' not in relevant_categories and 'qa' in self.categories:
            relevant_categories.append('qa')

        print(f"[Query Classification] Searching categories: {relevant_categories}")

        # Stage 2: Search in relevant categories
        all_results = []
        for category in relevant_categories:
            category_results = self.search_category(category, query, k=k, min_score=min_score)
            all_results.extend(category_results)

        # Stage 3: Keyword boost for recency queries
        query_lower = query.lower()
        recency_keywords = ['최신', 'latest', 'recent', '최근', '새로운', 'new', '2026', '2025']
        if any(kw in query_lower for kw in recency_keywords):
            # Search for recent publications by keyword matching
            if 'publications' in self.category_docs:
                for doc in self.category_docs['publications']:
                    content = doc['content'].lower()
                    # Boost documents with 2026 or 2025
                    if '2026' in content or 'wacv26' in content.lower():
                        existing = [r for r in all_results if r['content'] == doc['content']]
                        if not existing:
                            all_results.append({
                                'content': doc['content'],
                                'metadata': doc.get('metadata', {}),
                                'score': 0.9,  # High score for recent papers
                                'category': 'publications'
                            })
                    elif '2025' in content or 'cvpr25' in content.lower():
                        existing = [r for r in all_results if r['content'] == doc['content']]
                        if not existing:
                            all_results.append({
                                'content': doc['content'],
                                'metadata': doc.get('metadata', {}),
                                'score': 0.8,
                                'category': 'publications'
                            })

        # Sort by score
        all_results.sort(key=lambda x: x['score'], reverse=True)

        # Return top k
        return all_results[:k]

    def format_context(self, search_results: List[Dict[str, Any]], language: str = 'ko') -> str:
        """Format search results into context string for AI"""
        if not search_results:
            return ""

        if language == 'ko':
            context = "다음은 Reality Lab의 관련 정보입니다:\n\n"
        else:
            context = "Here is relevant information about Reality Lab:\n\n"

        for i, result in enumerate(search_results, 1):
            category = result.get('category', 'unknown')
            context += f"[참고자료 {i} - {category}]\n{result['content']}\n\n"

        return context.strip()


def test_retriever():
    """Test the hierarchical retriever"""
    retriever = HierarchicalRetriever(str(Path(__file__).resolve().parent / "hierarchical_rag"))
    retriever.load()

    # Test queries
    test_queries = [
        "연구원은 몇 명인가요?",
        "김희원 교수님 이메일이 뭐예요?",
        "CVPR 2025에 accept된 논문 있어요?",
        "졸업생은 몇 명인가요?",
        "최신 뉴스 알려주세요",
    ]

    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")

        results = retriever.search(query, k=2)

        for i, result in enumerate(results, 1):
            print(f"\n{i}. [Score: {result['score']:.4f}] [{result['category']}]")
            print(f"   {result['content'][:150]}...")


if __name__ == "__main__":
    test_retriever()
