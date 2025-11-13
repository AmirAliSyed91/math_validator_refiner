from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.services.agents import SupervisorAgent
from app.services.embeddings import QuestionIndexer

app = FastAPI(
    title="Math Question Assistant - Multi-Agent System",
    description="Validate, refine, and check similarity of math questions using Multi-Agent Architecture.",
    version="3.0.0",
)

supervisor_agent = SupervisorAgent()

indexer = None


def get_indexer():
    """Lazy initialization of the question indexer"""
    global indexer
    if indexer is None:
        indexer = QuestionIndexer("questions.json")
    return indexer


class ChatMessage(BaseModel):
    role: str
    content: str


class QuestionInput(BaseModel):
    question: str
    chat_history: List[ChatMessage] = []


@app.post("/process")
async def process_question(payload: QuestionInput):
    """
    Complete pipeline: Validates -> Refines (if needed) -> Checks Similarity
    
    This single endpoint handles all three use cases WITH chat history support:
    
    1. VALID Mathematical Question
       - Question is properly formatted
       - Returns refined version (if minor improvements made)
       - Shows similar questions
    
    2. REFINEABLE Mathematical Question
       - Question is mathematical but poorly formatted
       - Automatically refines and improves it
       - Shows changes made
       - Shows similar questions
    
    3. INVALID Non-Mathematical Question
       - Question is not mathematical
       - Cannot be refined
       - Rejects with clear error message
    
    Chat History:
        - Maintains conversation context
        - Supports follow-up questions
        - Allows refinement requests
    
    Returns:
        JSON response with status, message, and relevant data
    """
    try:
        history = [{"role": msg.role, "content": msg.content} for msg in payload.chat_history]
        
        result = await supervisor_agent.process(payload.question, chat_history=history)

        status = result.get("status")
        
        if status == "guardrail":
            return {
                "stage": "guardrail",
                "status": "guardrail",
                "original_question": payload.question,
                "message": result.get("message", ""),
                "is_guardrail": True,
            }

        if status == "invalid":
            return {
                "stage": "validation",
                "status": "invalid",
                "is_mathematical": result.get("is_mathematical", False),
                "original_question": payload.question,
                "reason": result.get("reason", "This is not a mathematical question"),
                "message": "This question is not mathematical and cannot be refined. Please ask a valid mathematical question.",
                "examples": [
                    "What is the derivative of x²?",
                    "How do you solve quadratic equations?",
                    "What is the Pythagorean theorem?",
                    "Calculate the area of a circle with radius 5"
                ]
            }

        refined_question = result.get("refined_question", payload.question)
        indexer = get_indexer()
        similarity_results = indexer.query(refined_question, threshold=0.8, top_k=5)

        if status == "valid":
            return {
                "stage": "completed",
                "status": "valid",
                "original_question": payload.question,
                "refined_question": refined_question,
                "changes": result.get("changes", []),
                "similar_questions": similarity_results,
                "message": "Valid mathematical question!",
            }
        else:
            return {
                "stage": "completed",
                "status": "refineable",
                "original_question": payload.question,
                "refined_question": refined_question,
                "changes": result.get("changes", []),
                "similar_questions": similarity_results,
                "reason": result.get("reason", "Question needed refinement"),
                "message": "Question was mathematical but needed refinement. See refined version and changes.",
            }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing question: {str(e)}"
        )
