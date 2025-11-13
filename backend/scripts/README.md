# Backend Scripts

This folder contains utility scripts for managing the backend infrastructure.

## build_faiss_index.py

Builds and persists the FAISS vector index from `questions.json`.

### Purpose
- Generates embeddings for all questions using OpenAI's embedding model
- Creates a FAISS index for semantic similarity search
- Saves the index to disk for fast loading on server startup

### Usage

```bash
# From the backend directory
cd /Users/macbookpro/Desktop/rag_test2/backend

# Activate virtual environment
source venv/bin/activate

# Run the script
python scripts/build_faiss_index.py
```

### Output Files

The script creates a `faiss_data/` directory with:
- `faiss_index.index` - The FAISS vector index
- `embeddings.npy` - The embedding vectors
- `questions_metadata.json` - Questions with metadata
- `index_info.json` - Index configuration information

### When to Run

Run this script whenever:
- You add new questions to `questions.json`
- You modify existing questions
- You want to rebuild the index with a different embedding model

### Prerequisites

- OpenAI API key set in `.env` file
- All Python dependencies installed (`pip install -r requirements.txt`)
- Virtual environment activated

### Notes

- The script automatically loads environment variables from `.env`
- Index building may take a few moments depending on the number of questions
- Once built, the server will automatically load the pre-built index for faster startup

