"""
TrueShift - Context Agent

Summarizes the user's current condition from available data.
This is the first agent called in most pipelines.
"""

from app.ai.agents.base_agent import (
    AgentContext,
    AgentResponse,
    BaseAgent,
)


class ContextAgent(BaseAgent):
    """
    Context Agent - Summarizes user's current condition.
    
    Purpose: Create a comprehensive summary of the user's state
    that other agents can use for decision making.
    """

    name = "context_agent"
    description = "Summarizes user's current condition from available data"
    version = "1.0.0"

    def get_agent_prompt(self) -> str:
        return """
        You are the Context Agent.
        
        Your responsibility is to:
        1. Analyze the user's current state data
        2. Identify key patterns and trends
        3. Summarize physical readiness (energy, fatigue, recovery)
        4. Note environmental context (location, time of day)
        5. Highlight any concerns or opportunities
        
        Output a structured summary that other agents can use.
        Be concise but comprehensive.
        """

    async def process(self, context: AgentContext) -> AgentResponse:
        """
        Process user context and generate a summary.
        """
        if not self.validate_context(context):
            return AgentResponse(
                agent_name=self.name,
                success=False,
                content="Invalid context provided",
                confidence=0.0,
            )

        # Extract key metrics from state
        state = context.user_state
        summary = await self._generate_summary(context)

        # Calculate readiness score
        readiness = self._calculate_readiness(state)

        return AgentResponse(
            agent_name=self.name,
            success=True,
            content={
                "summary": summary,
                "readiness_score": readiness["score"],
                "readiness_factors": readiness["factors"],
                "key_observations": self._get_observations(state),
                "recommended_focus": self._get_recommended_focus(state),
            },
            reasoning=f"Analyzed user state with {len(state)} data points",
            confidence=0.85,
            metadata={
                "state_completeness": self._calculate_completeness(state),
            },
        )

    async def _generate_summary(self, context: AgentContext) -> str:
        """
        Generate a natural language summary using LLM.
        """
        state = context.user_state

        # For development/fallback, generate rule-based summary
        if self.model is None:
            return self._rule_based_summary(state)

        prompt = """
        Analyze this user's current state and provide a brief summary (2-3 sentences)
        covering their physical readiness, recent activity, and any notable patterns.
        """

        return await self._call_llm(prompt, context, temperature=0.5)

    def _rule_based_summary(self, state: dict) -> str:
        """
        Generate summary using rules when LLM is unavailable.
        """
        parts = []

        # Physical status
        physical = state.get("physical", {})
        recovery = physical.get("recovery_status", "unknown")
        if recovery in ["exhausted", "fatigued"]:
            parts.append("User appears to need rest and recovery")
        elif recovery in ["fully_recovered", "well_rested"]:
            parts.append("User is well-rested and ready for activity")
        else:
            parts.append("User is in moderate condition")

        # Activity level
        steps = physical.get("steps_today", 0)
        if steps < 2000:
            parts.append(f"Low activity today with only {steps} steps")
        elif steps > 8000:
            parts.append(f"Active day with {steps} steps")

        # Location context
        location = state.get("location", {})
        loc_context = location.get("context", "unknown")
        if loc_context != "unknown":
            parts.append(f"Currently at {loc_context}")

        return ". ".join(parts) + "."

    def _calculate_readiness(self, state: dict) -> dict:
        """
        Calculate overall readiness score (0-100).
        """
        factors = {}
        score = 70  # Base score

        physical = state.get("physical", {})

        # Recovery factor
        recovery = physical.get("recovery_status", "moderate")
        recovery_scores = {
            "fully_recovered": 100,
            "well_rested": 85,
            "moderate": 65,
            "fatigued": 40,
            "exhausted": 20,
        }
        factors["recovery"] = recovery_scores.get(recovery, 65)

        # Sleep factor
        sleep = physical.get("sleep_hours")
        if sleep:
            if sleep >= 7:
                factors["sleep"] = 90
            elif sleep >= 6:
                factors["sleep"] = 70
            else:
                factors["sleep"] = 40

        # Activity balance
        workouts = physical.get("workouts_this_week", 0)
        if 3 <= workouts <= 5:
            factors["training_load"] = 85
        elif workouts < 3:
            factors["training_load"] = 70
        else:
            factors["training_load"] = 50

        # Calculate weighted average
        if factors:
            score = sum(factors.values()) / len(factors)

        return {
            "score": round(score),
            "factors": factors,
        }

    def _get_observations(self, state: dict) -> list[str]:
        """
        Extract key observations from state.
        """
        observations = []
        physical = state.get("physical", {})
        digital = state.get("digital", {})

        # Check sleep
        sleep = physical.get("sleep_hours")
        if sleep and sleep < 6:
            observations.append(f"Sleep deficit: only {sleep:.1f} hours last night")

        # Check screen time
        screen_time = digital.get("screen_time_minutes", 0)
        if screen_time > 300:
            observations.append(f"High screen time: {screen_time // 60}+ hours today")

        # Check workout streak
        workouts = physical.get("workouts_this_week", 0)
        if workouts >= 5:
            observations.append(f"Strong workout consistency: {workouts} sessions this week")
        elif workouts == 0:
            observations.append("No workouts recorded this week")

        return observations

    def _get_recommended_focus(self, state: dict) -> str:
        """
        Determine recommended focus area.
        """
        physical = state.get("physical", {})
        recovery = physical.get("recovery_status", "moderate")

        if recovery in ["exhausted", "fatigued"]:
            return "recovery"
        elif physical.get("workouts_this_week", 0) < 3:
            return "consistency"
        elif physical.get("active_minutes", 0) < 30:
            return "movement"
        else:
            return "performance"

    def _calculate_completeness(self, state: dict) -> float:
        """
        Calculate how complete the user state data is.
        """
        expected_fields = [
            "physical",
            "location",
            "digital",
            "goals",
        ]
        present = sum(1 for f in expected_fields if state.get(f))
        return present / len(expected_fields)
