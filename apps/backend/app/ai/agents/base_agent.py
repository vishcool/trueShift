"""
TrueShift - Base Agent

Abstract base class for all AI agents.
Following Google ADK patterns - agents are modular, stateless, and context-driven.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

from app.core.config import settings


class AgentContext(BaseModel):
    """
    Context provided to agents for decision making.
    """
    user_id: str
    user_state: dict  # Serialized UserState
    recent_events: list[dict] = Field(default_factory=list)
    conversation_history: list[dict] = Field(default_factory=list)
    additional_context: dict = Field(default_factory=dict)


class AgentResponse(BaseModel):
    """
    Standard response from agents.
    """
    agent_name: str
    success: bool
    content: Any
    reasoning: Optional[str] = None
    confidence: float = 0.0
    suggestions: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class BaseAgent(ABC):
    """
    Abstract base class for all TrueShift agents.
    
    Design principles (Google ADK style):
    - Stateless: No internal state between calls
    - Context-driven: All decisions based on provided context
    - Modular: Single responsibility per agent
    - Safe: Never provide medical diagnosis
    """

    # Agent identification
    name: str = "base_agent"
    description: str = "Base agent class"
    version: str = "1.0.0"

    # Safety guidelines
    SAFETY_PROMPT = """
    CRITICAL SAFETY RULES:
    - Never provide medical diagnosis or treatment advice
    - Always recommend consulting professionals for health concerns
    - Prioritize safety over performance
    - Be conservative with exercise intensity recommendations
    - Consider recovery and injury risk
    """

    # Base system prompt
    SYSTEM_PROMPT = """
    You are an AI fitness and digital wellbeing coach for TrueShift.
    
    Your role:
    - Provide helpful, actionable coaching advice
    - Always use provided user context
    - Be concise and clear
    - Ask for clarification if uncertain
    - Prioritize safety and sustainability
    
    {safety_rules}
    
    {agent_specific_prompt}
    """

    def __init__(self):
        """Initialize the agent with Gemini client."""
        self._init_client()

    def _init_client(self) -> None:
        """Initialize the Gemini API client."""
        if settings.google_api_key:
            self.client = genai.Client(api_key=settings.google_api_key)
            self.model_name = settings.gemini_model
        else:
            self.client = None
            self.model_name = None

    def _get_system_prompt(self) -> str:
        """Build the full system prompt."""
        return self.SYSTEM_PROMPT.format(
            safety_rules=self.SAFETY_PROMPT,
            agent_specific_prompt=self.get_agent_prompt(),
        )

    @abstractmethod
    def get_agent_prompt(self) -> str:
        """
        Return agent-specific prompt additions.
        Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    async def process(self, context: AgentContext) -> AgentResponse:
        """
        Process the given context and return a response.
        Must be implemented by subclasses.
        """
        pass

    async def _call_llm(
        self,
        prompt: str,
        context: AgentContext,
        temperature: float = 0.7,
    ) -> str:
        """
        Make a call to the Gemini LLM.
        """
        if self.client is None:
            # Fallback for development without API key
            return self._dev_fallback(prompt, context)

        try:
            # Build the full prompt with context
            full_prompt = f"""
{self._get_system_prompt()}

USER CONTEXT:
{self._format_context(context)}

TASK:
{prompt}
"""
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=1024,
                ),
            )
            return response.text

        except Exception as e:
            print(f"LLM call failed: {e}")
            return self._dev_fallback(prompt, context)

    def _format_context(self, context: AgentContext) -> str:
        """Format context for the LLM."""
        lines = [
            f"User ID: {context.user_id}",
            "",
            "Current State:",
        ]
        for key, value in context.user_state.items():
            lines.append(f"  {key}: {value}")

        if context.additional_context:
            lines.append("")
            lines.append("Additional Context:")
            for key, value in context.additional_context.items():
                lines.append(f"  {key}: {value}")

        return "\n".join(lines)

    def _dev_fallback(self, prompt: str, context: AgentContext) -> str:
        """
        Development fallback when no API key is available.
        Returns a placeholder response.
        """
        return f"[DEV MODE] Agent {self.name} would process: {prompt[:100]}..."

    def validate_context(self, context: AgentContext) -> bool:
        """
        Validate that required context is present.
        Can be overridden by subclasses for specific requirements.
        """
        return bool(context.user_id and context.user_state)
