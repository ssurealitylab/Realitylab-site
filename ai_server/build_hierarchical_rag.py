#!/usr/bin/env python3
"""
Build Hierarchical RAG System
Organizes knowledge base into category-specific folders/indexes
"""

import json
import pickle
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
import faiss
from typing import Dict, List

class HierarchicalRAGBuilder:
    def __init__(self, knowledge_base_path: str, output_dir: str):
        self.kb_path = Path(knowledge_base_path)
        self.output_dir = Path(output_dir)
        self.model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        self.model = None
        self.documents = []

        # Category mapping
        self.categories = {
            "members": ["member"],
            "news": ["news"],
            "publications": ["publication"],
            "lab_info": ["lab_info"],
            "research": ["research_area"],
            "qa": ["qa"]
        }

    def load_knowledge_base(self):
        """Load knowledge base"""
        print(f"Loading knowledge base from: {self.kb_path}")
        with open(self.kb_path, 'r', encoding='utf-8') as f:
            self.documents = json.load(f)
        print(f"  Loaded {len(self.documents)} documents")

    def load_embedding_model(self):
        """Load sentence transformer model"""
        print(f"\nLoading embedding model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        print(f"  Model loaded successfully")

    def build_category_index(self, category_name: str, doc_types: List[str]):
        """Build FAISS index for a specific category"""
        print(f"\n=== Building {category_name} Index ===")

        # Filter documents for this category
        category_docs = [
            doc for doc in self.documents
            if doc['metadata']['type'] in doc_types
        ]

        if not category_docs:
            print(f"  No documents found for {category_name}")
            return

        print(f"  Documents: {len(category_docs)}")

        # Create embeddings
        texts = [doc['content'] for doc in category_docs]
        embeddings = self.model.encode(
            texts,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        # Build FAISS index
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)
        index.add(embeddings.astype('float32'))

        # Save category folder
        category_dir = self.output_dir / category_name
        category_dir.mkdir(parents=True, exist_ok=True)

        # Save index
        index_file = category_dir / "faiss_index.bin"
        faiss.write_index(index, str(index_file))

        # Save documents
        docs_file = category_dir / "documents.pkl"
        with open(docs_file, 'wb') as f:
            pickle.dump(category_docs, f)

        # Save config
        config = {
            "category": category_name,
            "model_name": self.model_name,
            "num_documents": len(category_docs),
            "embedding_dim": dimension,
            "doc_types": doc_types
        }
        config_file = category_dir / "config.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"  ✅ Saved to: {category_dir}")
        print(f"     Index: {index.ntotal} vectors")

    def build_all_categories(self):
        """Build indexes for all categories"""
        print("\n" + "="*60)
        print("Building Hierarchical RAG System")
        print("="*60)

        for category_name, doc_types in self.categories.items():
            self.build_category_index(category_name, doc_types)

        # Also save category metadata
        metadata = {
            "categories": list(self.categories.keys()),
            "model_name": self.model_name,
            "total_documents": len(self.documents)
        }
        metadata_file = self.output_dir / "categories.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        print("\n" + "="*60)
        print("✅ Hierarchical RAG Build Complete!")
        print(f"Output directory: {self.output_dir}")
        print("="*60)

    def build(self):
        """Build complete hierarchical RAG system"""
        self.load_knowledge_base()
        self.load_embedding_model()
        self.build_all_categories()


def main():
    here = Path(__file__).resolve().parent
    kb_path = str(here / "knowledge_base.json")
    output_dir = str(here / "hierarchical_rag")

    builder = HierarchicalRAGBuilder(kb_path, output_dir)
    builder.build()


if __name__ == "__main__":
    main()
