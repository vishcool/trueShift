"""
TrueShift - Recovery Agent

Specialized agent for physical recovery, sleep coaching, and injury prevention.
"""

from app.ai.agents.base_agent import (
    AgentContext,
    AgentResponse,
    BaseAgent,
)


class RecoveryAgent(BaseAgent):
    """
    Recovery Agent - Optimizes rest and recovery.
    """

    name = "recovery_agent"
    description = "Manages sleep coaching and physical recovery protocols"
    version = "1.0.0"

    def get_agent_prompt(self) -> str:
        return """
        You are the Recovery Agent.
        
        Your goals:
        1. Analyze sleep quality and recovery status.
        2. If 'fatigued' or 'exhausted' -> suggest active recovery or sleep hygiene tips.
        3. If specific pain is logged -> suggest safe mobility work (avoiding the injured area) or rest.
        4. Optimize the user's readiness for tomorrow.
        
        Safety:
        - Never diagnose injuries.
        - If pain is 'sharp' or high severity (>7/10), recommend seeing a doctor.
        """

    async def process(self, context: AgentContext) -> AgentResponse:
        """
        Generate recovery recommendations.
        """
        if not self.validate_context(context):
            return AgentResponse(
                agent_name=self.name,
                success=False,
                content="Invalid context",
            )

        prompt = """
        Review the user's recovery status, sleep logs, and any pain reports.
        Provide:
        1. An assessment of their recovery status.
        2. A specific recommendation (e.g., 'Sleep 30min earlier', 'Do 10min foam rolling').
        3. A "Readiness Score" adjustment suggestion if needed.
        """
        
        response_text = await self._call_llm(prompt, context, temperature=0.4)
        
        return AgentResponse(
            agent_name=self.name,
            success=True,
            content={"advice": response_text},
            reasoning="Analyzed sleep and recovery metrics",
            confidence=0.85
        )
