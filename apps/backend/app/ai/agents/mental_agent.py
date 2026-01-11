"""
TrueShift - Mental Wellness Agent

Specialized agent for mental health, stress management, and mindfulness.
"""

from app.ai.agents.base_agent import (
    AgentContext,
    AgentResponse,
    BaseAgent,
)


class MentalWellnessAgent(BaseAgent):
    """
    Mental Wellness Agent - Focuses on stress, mood, and mindfulness.
    """

    name = "mental_wellness_agent"
    description = "Provides guidance on stress management and mindfulness"
    version = "1.0.0"

    def get_agent_prompt(self) -> str:
        return """
        You are the Mental Wellness Agent.
        
        Your goals:
        1. Analyze user's mood logs and stress levels.
        2. high stress -> suggest short breathing exercises or meditation.
        3. Low energy -> suggest uplifting activities or rest.
        4. Provide empathetic, non-clinical support.
        
        CRITICAL: 
        - If the user indicates self-harm or severe depression, output a hard safety warning and refer to professional help immediately.
        - Do NOT attempt to treat clinical conditions.
        """

    async def process(self, context: AgentContext) -> AgentResponse:
        """
        Generate mental wellness advice.
        """
        if not self.validate_context(context):
            return AgentResponse(
                agent_name=self.name,
                success=False,
                content="Invalid context",
            )

        # Check for safety flags in context (mock check)
        # In real impl, we'd check specific mood keywords
        
        prompt = """
        Based on the user's recent mood logs and context summary, provide:
        1. A brief observation of their mental state.
        2. One specific mindfulness or stress-relief technique to try today.
        3. A supportive message.
        """
        
        response_text = await self._call_llm(prompt, context, temperature=0.6)
        
        return AgentResponse(
            agent_name=self.name,
            success=True,
            content={"advice": response_text},
            reasoning="Analyzed mood and stress context",
            confidence=0.8
        )
