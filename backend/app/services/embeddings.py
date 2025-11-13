import json
import os
from pathlib import Path

import faiss
import numpy as np
from langchain_openai import OpenAIEmbeddings


class QuestionIndexer:
    """
    Indexes mathematical questions from a JSON file using FAISS
    and allows semantic similarity-based retrieval.
    
    Supports loading pre-built index from disk for faster startup.
    """

    def __init__(self, json_path: str, model_name: str = "text-embedding-3-small", index_dir: str = None):
        self.json_path = json_path
        self.model_name = model_name
        self.embeddings_model = OpenAIEmbeddings(model=model_name)
        self.index_dir = index_dir or str(Path(json_path).parent / "faiss_data")
        self.questions = None
        self.index = None
        self.embeddings = None
        
        if not self.load_index():
            self.questions = self._load_questions()
            self.build_index()

    def _load_questions(self):
        """Load questions from JSON file."""
        with open(self.json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("JSON file must contain a list of question objects.")
        return data

    def load_index(self):
        """
        Load pre-built FAISS index from disk if available.
        Returns True if successful, False otherwise.
        """
        index_path = os.path.join(self.index_dir, "faiss_index.index")
        embeddings_path = os.path.join(self.index_dir, "embeddings.npy")
        metadata_path = os.path.join(self.index_dir, "questions_metadata.json")
        
        if not (os.path.exists(index_path) and 
                os.path.exists(embeddings_path) and 
                os.path.exists(metadata_path)):
            print("Pre-built index not found. Building from scratch...")
            return False
        
        try:
            print("Loading pre-built FAISS index from disk...")
            
            self.index = faiss.read_index(index_path)
            self.embeddings = np.load(embeddings_path)
            
            with open(metadata_path, "r", encoding="utf-8") as f:
                self.questions = json.load(f)
            
            print(f"Loaded index with {len(self.questions)} questions successfully.")
            return True
            
        except Exception as e:
            print(f"Error loading pre-built index: {e}")
            print("Building index from scratch...")
            return False

    def build_index(self):
        """Compute embeddings and create a FAISS index for the questions."""
        print("Building FAISS index for questions...")

        question_texts = [q["question"] for q in self.questions]

        self.embeddings = np.array(self.embeddings_model.embed_documents(question_texts)).astype(
            "float32"
        )

        dim = self.embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)

        faiss.normalize_L2(self.embeddings)
        self.index.add(self.embeddings)

        print(f"Indexed {len(self.questions)} questions successfully.")

    def query(self, query_text: str, threshold: float = 0.8, top_k: int = 5):
        """
        Query for semantically similar questions.
        Returns a list of results with similarity score > threshold.
        """
        query_emb = (
            np.array(self.embeddings_model.embed_query(query_text)).astype("float32").reshape(1, -1)
        )
        faiss.normalize_L2(query_emb)

        scores, indices = self.index.search(query_emb, top_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            similarity = float(score)
            if similarity >= threshold:
                q_data = self.questions[idx].copy()
                q_data["similarity"] = round(similarity * 100, 2)
                results.append(q_data)

        return results
