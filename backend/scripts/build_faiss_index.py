#!/usr/bin/env python3
"""
Script to build and persist FAISS index from questions.json

This script:
1. Loads questions from questions.json
2. Generates embeddings using OpenAI embedding model
3. Creates a FAISS index
4. Saves the index and metadata to disk

Usage:
    python scripts/build_faiss_index.py
"""

import json
import os
import sys
from pathlib import Path

import faiss
import numpy as np
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

backend_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_path))

load_dotenv()


def build_and_save_index(
    questions_path: str,
    index_dir: str,
    model_name: str = "text-embedding-3-small"
):
    """
    Build FAISS index from questions.json and save to disk.
    
    Args:
        questions_path: Path to questions.json file
        index_dir: Directory to save the index files
        model_name: OpenAI embedding model name
    """
    print("=" * 80)
    print("Building FAISS Index for Mathematical Questions")
    print("=" * 80)
    
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not found in environment variables")
        print("Please set OPENAI_API_KEY in your .env file")
        sys.exit(1)
    
    print(f"\n[1/5] Loading questions from: {questions_path}")
    try:
        with open(questions_path, "r", encoding="utf-8") as f:
            questions = json.load(f)
        
        if not isinstance(questions, list):
            raise ValueError("questions.json must contain a list of question objects")
        
        print(f"      Loaded {len(questions)} questions")
    except FileNotFoundError:
        print(f"ERROR: File not found: {questions_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {questions_path}: {e}")
        sys.exit(1)
    
    print(f"\n[2/5] Initializing OpenAI Embeddings model: {model_name}")
    embeddings_model = OpenAIEmbeddings(model=model_name)
    
    print(f"\n[3/5] Extracting question texts")
    question_texts = [q["question"] for q in questions]
    
    print(f"\n[4/5] Generating embeddings (this may take a moment)...")
    try:
        embeddings = np.array(
            embeddings_model.embed_documents(question_texts)
        ).astype("float32")
        print(f"      Generated embeddings with shape: {embeddings.shape}")
    except Exception as e:
        print(f"ERROR: Failed to generate embeddings: {e}")
        sys.exit(1)
    
    print(f"\n[5/5] Building FAISS index")
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    
    faiss.normalize_L2(embeddings)
    index.add(embeddings)
    
    print(f"      Indexed {index.ntotal} vectors")
    
    os.makedirs(index_dir, exist_ok=True)
    
    index_path = os.path.join(index_dir, "faiss_index.index")
    print(f"\n[SAVE] Writing FAISS index to: {index_path}")
    faiss.write_index(index, index_path)
    
    embeddings_path = os.path.join(index_dir, "embeddings.npy")
    print(f"[SAVE] Writing embeddings to: {embeddings_path}")
    np.save(embeddings_path, embeddings)
    
    metadata_path = os.path.join(index_dir, "questions_metadata.json")
    print(f"[SAVE] Writing questions metadata to: {metadata_path}")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)
    
    info = {
        "num_questions": len(questions),
        "embedding_model": model_name,
        "embedding_dimension": dim,
        "index_type": "IndexFlatIP",
        "questions_source": questions_path
    }
    info_path = os.path.join(index_dir, "index_info.json")
    print(f"[SAVE] Writing index info to: {info_path}")
    with open(info_path, "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2)
    
    print("\n" + "=" * 80)
    print("FAISS Index Build Complete!")
    print("=" * 80)
    print(f"\nFiles created:")
    print(f"  - {index_path}")
    print(f"  - {embeddings_path}")
    print(f"  - {metadata_path}")
    print(f"  - {info_path}")
    print(f"\nTotal questions indexed: {len(questions)}")
    print(f"Embedding dimension: {dim}")
    print("\nYou can now use these files to load the index quickly on server startup.")
    print("=" * 80)


if __name__ == "__main__":
    backend_root = Path(__file__).resolve().parent.parent
    questions_file = backend_root / "questions.json"
    index_directory = backend_root / "faiss_data"
    
    print(f"\nBackend root: {backend_root}")
    print(f"Questions file: {questions_file}")
    print(f"Index directory: {index_directory}\n")
    
    build_and_save_index(
        questions_path=str(questions_file),
        index_dir=str(index_directory),
        model_name="text-embedding-3-small"
    )

