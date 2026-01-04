"""
TrueShift - AI Orchestrator

Coordinates multi-agent AI processing pipelines.
Following Google ADK patterns for agent orchestration.
"""

from typing import Any, Optional
from datetime import datetime, timezone

from app.ai.agents.base_agent import AgentContext, AgentResponse
from app.ai.agents.context_agent import ContextAgent
from app.ai.agents.coaching_agent import CoachingAgent
from app.ai.agents.workout_agent import WorkoutAgent
from app.models.user_state import UserState


class OrchestratorResult:
    """
    Result from the orchestrator containing all agent outputs.
    """

    def __init__(
        self,
        user_id: str,
        timestamp: datetime,
        context_summary: Optional[dict] = None,
        coaching: Optional[dict] = None,
        workout: Optional[dict] = None,
        errors: list[str] = None,
    ):
        self.user_id = user_id
        self.timestamp = timestamp
        self.context_summary = context_summary
        self.coaching = coaching
        self.workout = workout
        self.errors = errors or []

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat(),
            "context_summary": self.context_summary,
            "coaching": self.coaching,
            "workout": self.workout,
            "errors": self.errors,
        }


class AIOrchestrator:
    """
    Central AI orchestrator that coordinates agent pipelines.
    
    Implements the multi-agent architecture where:
    1. Context Agent runs first to summarize state
    2. Other agents receive enriched context
    3. Results are aggregated and returned
    """

    def __init__(self):
        # Initialize agents
        self.context_agent = ContextAgent()
        self.coaching_agent = CoachingAgent()
        self.workout_agent = WorkoutAgent()

    async def process_full_pipeline(
        self,
        user_id: str,
        user_state: UserState,
        recent_events: list[dict] = None,
        additional_context: dict = None,
    ) -> OrchestratorResult:
        """
        Run the full agent pipeline.
        
        Pipeline:
        1. Context Agent → State summary
        2. Coaching Agent → Personalized advice (parallel)
        3. Workout Agent → Workout recommendations (parallel)
        """
        errors = []
        
        # Build initial context
        context = AgentContext(
            user_id=user_id,
            user_state=user_state.get_context_summary() if hasattr(user_state, 'get_context_summary') else user_state,
            recent_events=recent_events or [],
            additional_context=additional_context or {},
        )

        # Step 1: Context Agent (runs first)
        context_result = await self._run_agent(
            self.context_agent,
            context,
            "Context Agent",
        )
        if not context_result.success:
            errors.append(f"Context Agent failed: {context_result.content}")

        # Enrich context with agent output
        if context_result.success and context_result.content:
            context.additional_context["context_summary"] = context_result.content

        # Step 2 & 3: Run coaching and workout agents (can be parallel)
        coaching_result = await self._run_agent(
            self.coaching_agent,
            context,
            "Coaching Agent",
        )
        if not coaching_result.success:
            errors.append(f"Coaching Agent failed: {coaching_result.content}")

        workout_result = await self._run_agent(
            self.workout_agent,
            context,
            "Workout Agent",
        )
        if not workout_result.success:
            errors.append(f"Workout Agent failed: {workout_result.content}")

        # Build result
        return OrchestratorResult(
            user_id=user_id,
            timestamp=datetime.now(timezone.utc),
            context_summary=context_result.content if context_result.success else None,
            coaching=coaching_result.content if coaching_result.success else None,
            workout=workout_result.content if workout_result.success else None,
            errors=errors,
        )

    async def get_coaching(
        self,
        user_id: str,
        user_state: UserState,
    ) -> AgentResponse:
        """
        Get coaching advice only.
        """
        context = AgentContext(
            user_id=user_id,
            user_state=user_state.get_context_summary() if hasattr(user_state, 'get_context_summary') else user_state,
        )
        return await self.coaching_agent.process(context)

    async def get_workout(
        self,
        user_id: str,
        user_state: UserState,
    ) -> AgentResponse:
        """
        Get workout recommendation only.
        """
        context = AgentContext(
            user_id=user_id,
            user_state=user_state.get_context_summary() if hasattr(user_state, 'get_context_summary') else user_state,
        )
        return await self.workout_agent.process(context)

    async def get_context_summary(
        self,
        user_id: str,
        user_state: UserState,
    ) -> AgentResponse:
        """
        Get context summary only.
        """
        context = AgentContext(
            user_id=user_id,
            user_state=user_state.get_context_summary() if hasattr(user_state, 'get_context_summary') else user_state,
        )
        return await self.context_agent.process(context)

    async def _run_agent(
        self,
        agent: Any,
        context: AgentContext,
        agent_name: str,
    ) -> AgentResponse:
        """
        Run a single agent with error handling.
        """
        try:
            return await agent.process(context)
        except Exception as e:
            return AgentResponse(
                agent_name=agent_name,
                success=False,
                content=f"Agent error: {str(e)}",
                confidence=0.0,
            )


# Global orchestrator instance
ai_orchestrator = AIOrchestrator()
