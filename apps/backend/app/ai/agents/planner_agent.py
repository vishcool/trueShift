"""
TrueShift - Planner Agent

Chooses the best specialist path for the user's current turn and state.
"""

from app.ai.agents.base_agent import AgentContext, AgentResponse, BaseAgent


class PlannerAgent(BaseAgent):
    """
    Lightweight planning agent that routes work to specialist agents.
    """

    name = "planner_agent"
    description = "Chooses the best specialist workflow for the current user turn"
    version = "1.0.0"

    def get_agent_prompt(self) -> str:
        return """
        You are the planning agent for a multimodal coaching system.

        Decide which specialist domain should lead the response:
        - workout
        - recovery
        - mental
        - nutrition
        - coaching
        """

    async def process(self, context: AgentContext) -> AgentResponse:
        if not self.validate_context(context):
            return AgentResponse(
                agent_name=self.name,
                success=False,
                content="Invalid context provided",
                confidence=0.0,
            )

        plan = self._build_rule_based_plan(context)
        return AgentResponse(
            agent_name=self.name,
            success=True,
            content=plan,
            reasoning=f"Primary domain selected: {plan['primary_domain']}",
            confidence=plan["confidence"],
            metadata={"delegates": plan["delegates"]},
        )

    def _build_rule_based_plan(self, context: AgentContext) -> dict:
        state = context.user_state.get("physical", {})
        user_input = str(context.additional_context.get("user_input", "")).lower()
        conversation_mode = str(context.additional_context.get("mode", "")).lower()
        recovery_status = state.get("recovery_status", "moderate")
        sleep_hours = state.get("sleep_hours")

        primary_domain = "coaching"
        goals: list[str] = ["support_user"]
        delegates = ["context", "coaching"]
        confidence = 0.65

        workout_terms = ("workout", "train", "session", "exercise", "legs", "push", "pull", "plan")
        nutrition_terms = ("diet", "meal", "macro", "protein", "calorie", "nutrition")
        mental_terms = ("stress", "anxiety", "motivation", "overwhelmed", "burnout")

        if conversation_mode == "diet" or any(term in user_input for term in nutrition_terms):
            primary_domain = "nutrition"
            goals = ["answer_nutrition_request", "tie_back_to_training"]
            delegates = ["context", "coaching"]
            confidence = 0.8
        elif recovery_status in {"fatigued", "exhausted"} or (sleep_hours is not None and sleep_hours < 6):
            primary_domain = "recovery"
            goals = ["reduce_risk", "adapt_training_load"]
            delegates = ["context", "recovery", "coaching"]
            confidence = 0.88
        elif conversation_mode == "workout" or any(term in user_input for term in workout_terms):
            primary_domain = "workout"
            goals = ["create_or_adjust_workout", "preserve_progression"]
            delegates = ["context", "workout", "coaching"]
            confidence = 0.86
        elif conversation_mode == "recovery":
            primary_domain = "recovery"
            goals = ["improve_recovery", "reduce_training_risk"]
            delegates = ["context", "recovery", "coaching"]
            confidence = 0.82
        elif any(term in user_input for term in mental_terms):
            primary_domain = "mental"
            goals = ["improve_adherence", "support_motivation"]
            delegates = ["context", "mental", "coaching"]
            confidence = 0.78

        return {
            "primary_domain": primary_domain,
            "goals": goals,
            "delegates": delegates,
            "confidence": confidence,
        }
