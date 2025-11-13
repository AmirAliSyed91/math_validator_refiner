"""
Multi-Agent System for Mathematical Question Processing

Architecture:
- SupervisorAgent: Routes questions to appropriate agent based on validation
- ValidationAgent: Classifies questions (valid/refineable/invalid) using ValidationChain WITH chat history
- RefinementAgent: Fixes mathematical questions using RefinementChain
- GuardrailAgent: Handles non-mathematical queries and maintains system focus using GuardrailChain
"""

import json
import re

from app.services.chains import GuardrailChain, RefinementChain, ValidationChain


class ValidationAgent:
    """Agent that validates and classifies mathematical questions using ValidationChain"""

    def __init__(self):
        self.chain = ValidationChain()

    async def classify(self, question: str, chat_history: list = None) -> dict:
        """
        Classify a question using the validation chain with chat history context
        
        Args:
            question: Current user question
            chat_history: Previous conversation messages for context
        """
        question_with_context = question
        if chat_history and len(chat_history) > 0:
            context_messages = chat_history[-4:]
            context = "Previous conversation:\n"
            for msg in context_messages:
                context += f"{msg['role']}: {msg['content']}\n"
            context += f"\nCurrent question: {question}"
            question_with_context = context

        response_raw = await self.chain.arun(question_with_context)
        cleaned = re.sub(r"```json\s*|\s*```", "", response_raw).strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Response content: {response_raw}")
            return {
                "status": "invalid",
                "reason": "Error parsing validation response",
                "is_mathematical": False,
            }


class RefinementAgent:
    """Agent that refines mathematical questions using RefinementChain"""

    def __init__(self):
        self.chain = RefinementChain()

    async def refine(self, question: str) -> dict:
        """Refine a mathematical question using the refinement chain"""
        response_raw = await self.chain.arun(question)
        cleaned = re.sub(r"```json\s*|\s*```", "", response_raw).strip()

        cleaned = cleaned.replace("\\(", "(").replace("\\)", ")")
        cleaned = cleaned.replace("\\[", "[").replace("\\]", "]")

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            print(f"JSON decode error in refinement: {e}")
            print(f"Response content: {response_raw}")
            return {
                "refined_question": question,
                "changes": ["Unable to refine - JSON parsing error"],
            }


class GuardrailAgent:
    """Agent that handles non-mathematical queries and maintains system guardrails with chat history"""

    def __init__(self):
        self.chain = GuardrailChain()

    async def respond(self, user_message: str, chat_history: list = None) -> str:
        """
        Generate a guardrail response with chat history context
        
        Used for:
        - Non-mathematical queries that need polite redirection
        - Follow-up questions that need conversation context
        - Casual conversation that should be redirected to math topics

        Args:
            user_message: Current user message
            chat_history: List of previous messages [{"role": "user"|"assistant", "content": "..."}]

        Returns:
            String response from the guardrail agent
        """
        return await self.chain.arun(user_message, chat_history)


class SupervisorAgent:
    """Supervisor agent that coordinates validation, refinement, and guardrails"""

    def __init__(self):
        self.validation_agent = ValidationAgent()
        self.refinement_agent = RefinementAgent()
        self.guardrail_agent = GuardrailAgent()

    async def process(self, question: str, chat_history: list = None) -> dict:
        """
        Process a question through the multi-agent system with chat history

        Args:
            question: User's input question
            chat_history: Optional chat history for conversational context

        Returns:
            dict with status, message, and optional refined_question
        """
        classification = await self.validation_agent.classify(question, chat_history)

        status = classification.get("status")
        reason = classification.get("reason", "")
        is_mathematical = classification.get("is_mathematical", False)

        if status == "valid":
            refinement = await self.refinement_agent.refine(question)

            return {
                "status": "valid",
                "message": f"VALID: {question}",
                "original_question": question,
                "refined_question": refinement.get("refined_question", question),
                "changes": refinement.get("changes", []),
                "is_mathematical": True,
            }

        elif status == "refineable":
            refinement = await self.refinement_agent.refine(question)

            return {
                "status": "refineable",
                "message": f"REFINEABLE: Mathematical but needs fixes",
                "original_question": question,
                "refined_question": refinement.get("refined_question", question),
                "changes": refinement.get("changes", []),
                "reason": reason,
                "is_mathematical": True,
            }

        else:
            if chat_history and len(chat_history) > 0:
                guardrail_response = await self.guardrail_agent.respond(question, chat_history)
                return {
                    "status": "guardrail",
                    "message": guardrail_response,
                    "original_question": question,
                    "is_mathematical": False,
                    "is_guardrail": True,
                }
            
            return {
                "status": "invalid",
                "message": f"INVALID: Not mathematical - unrefineable",
                "original_question": question,
                "reason": reason,
                "is_mathematical": False,
                "error": "This question is not mathematical and cannot be refined. Please ask a valid mathematical question.",
            }
