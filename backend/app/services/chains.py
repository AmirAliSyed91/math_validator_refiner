import os

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.core.prompts import GUARDRAIL_PROMPT, REFINEMENT_PROMPT, VALIDATION_PROMPT

LLM_MODEL = os.getenv("MODEL_NAME", "gpt-4o-mini")


class ValidationChain:
    """Chain that validates if a user question is a valid mathematical question."""

    def __init__(self, temperature: float = 0.0):
        self.llm = ChatOpenAI(model=LLM_MODEL, temperature=temperature)
        self.prompt = ChatPromptTemplate.from_template(VALIDATION_PROMPT)
        self.parser = JsonOutputParser()

    async def arun(self, user_question: str):
        """Run validation chain on user question."""
        formatted_prompt = self.prompt.format(user_question=user_question)
        response = await self.llm.ainvoke(formatted_prompt)
        return response.content


class RefinementChain:
    """Chain that refines and improves the clarity of valid math questions."""

    def __init__(self, temperature: float = 0.0):
        self.llm = ChatOpenAI(model=LLM_MODEL, temperature=temperature)
        self.prompt = ChatPromptTemplate.from_template(REFINEMENT_PROMPT)
        self.parser = JsonOutputParser()

    async def arun(self, valid_question: str):
        """Run refinement chain on a valid math question."""
        formatted_prompt = self.prompt.format(valid_question=valid_question)
        response = await self.llm.ainvoke(formatted_prompt)
        return response.content


class GuardrailChain:
    """Chain that handles guardrails for non-mathematical queries with chat history context."""

    def __init__(self, temperature: float = 0.7):
        self.llm = ChatOpenAI(model=LLM_MODEL, temperature=temperature)

    async def arun(self, user_message: str, chat_history: list = None):
        """
        Run guardrail chain with chat history using GUARDRAIL_PROMPT.

        Args:
            user_message: Current user message
            chat_history: List of previous messages [{"role": "user"|"assistant", "content": "..."}]
        """
        system_content = GUARDRAIL_PROMPT.replace("{user_message}", user_message)
        
        messages = [
            SystemMessage(content=system_content)
        ]

        if chat_history:
            for msg in chat_history[-10:]:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))

        messages.append(HumanMessage(content=user_message))

        response = await self.llm.ainvoke(messages)
        return response.content
