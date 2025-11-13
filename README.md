# Math Question Assistant

A chatbot that validates and refines mathematical questions, then checks for similar questions in a database.

## What it does

The system takes a user's question and:
1. Checks if it's actually a math question
2. Fixes formatting/grammar issues if needed
3. Searches for similar questions in the database
4. Returns everything with explanations

## Stack

**Backend**
- FastAPI (Python)
- LangChain with OpenAI GPT-4o-mini
- FAISS for vector similarity search
- Multi-agent architecture (validation + refinement agents)

**Frontend**
- React + Vite
- Axios for API calls
- Basic CSS styling

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/main.py          # FastAPI endpoints
│   │   ├── services/
│   │   │   ├── agents.py        # Multi-agent system
│   │   │   ├── chains.py        # LangChain LLM chains
│   │   │   └── embeddings.py    # FAISS indexing
│   │   └── core/prompts.py      # System prompts
│   ├── questions.json           # Question database
│   ├── faiss_data/              # Vector embeddings
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Main chat UI
│   │   └── App.css
│   ├── nginx.conf               # Production nginx config
│   ├── package.json
│   └── Dockerfile
└── docker-compose.yml
```

## Setup

### Local Development

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Add your OpenAI key
echo "OPENAI_API_KEY=your_key_here" > .env

# Run server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### Docker (Production)

```bash
# Set your OpenAI key
export OPENAI_API_KEY="your_key_here"

# Build and run
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop
docker-compose down
```

Access:
- Frontend: http://localhost
- Backend API: http://localhost:8000/docs

## How it works

### Multi-Agent System

**Supervisor Agent** → orchestrates the flow

**Validation Agent** → checks if question is mathematical
- Valid → proceed to refinement
- Invalid → reject with examples

**Refinement Agent** → improves the question
- Fixes grammar, notation, clarity
- Returns list of changes made

**Similarity Search** → finds related questions using FAISS

### API Endpoint

`POST /process`

Request:
```json
{
  "question": "whats the derivitive of x squared",
  "chat_history": [
    {"role": "user", "content": "previous question"},
    {"role": "assistant", "content": "previous response"}
  ]
}
```

Response (refineable):
```json
{
  "status": "refineable",
  "original_question": "whats the derivitive of x squared",
  "refined_question": "What is the derivative of x²?",
  "changes": [
    "Fixed spelling: 'derivitive' → 'derivative'",
    "Corrected notation: 'x squared' → 'x²'"
  ],
  "similar_questions": [
    {
      "question": "How do you find the derivative of x³?",
      "similarity": 85,
      "domain": "Calculus",
      "subdomain": "Derivatives"
    }
  ]
}
```

## Building FAISS Index

If you modify `questions.json`:

```bash
cd backend
python scripts/build_faiss_index.py
```

This regenerates embeddings in `faiss_data/`.

## Environment Variables

Required:
- `OPENAI_API_KEY` - Your OpenAI API key

Optional (backend):
- `MODEL_NAME` - Default: `gpt-4o-mini`
- `ENVIRONMENT` - Default: `development`
- `LOG_LEVEL` - Default: `INFO`

## Notes

- Questions must be mathematical to pass validation
- Non-math questions get rejected with helpful examples
- Chat history is maintained for follow-up questions
- FAISS threshold is 0.8 (80% similarity) by default
- Frontend proxies `/api/*` to backend through nginx in production

