"""
TrueShift - Coaching Agent

Provides personalized coaching advice based on user context.
"""

from app.ai.agents.base_agent import (
    AgentContext,
    AgentResponse,
    BaseAgent,
)


class CoachingAgent(BaseAgent):
    """
    Coaching Agent - Provides actionable coaching advice.
    
    Purpose: Generate personalized, motivational coaching
    based on user's goals and current state.
    """

    name = "coaching_agent"
    description = "Provides personalized coaching and motivation"
    version = "1.0.0"

    def get_agent_prompt(self) -> str:
        return """
        You are a supportive, knowledgeable fitness and wellbeing coach.
        
        Your style:
        - Encouraging but realistic
        - Focus on sustainable habits
        - Celebrate small wins
        - Provide specific, actionable advice
        - Adapt tone to user's current state (gentler when tired, motivating when energized)
        
        Never:
        - Shame or guilt the user
        - Push through pain or exhaustion
        - Recommend extreme measures
        - Provide medical advice
        """

    async def process(self, context: AgentContext) -> AgentResponse:
        """
        Generate coaching advice based on context.
        """
        if not self.validate_context(context):
            return AgentResponse(
                agent_name=self.name,
                success=False,
                content="Invalid context provided",
                confidence=0.0,
            )

        state = context.user_state

        # Determine coaching approach based on state
        approach = self._determine_approach(state)

        # Generate coaching message
        message = await self._generate_coaching(context, approach)

        # Generate action items
        actions = self._generate_actions(state, approach)

        return AgentResponse(
            agent_name=self.name,
            success=True,
            content={
                "message": message,
                "approach": approach,
                "actions": actions,
                "tone": self._get_tone(state),
            },
            reasoning=f"Coaching approach: {approach}",
            confidence=0.8,
            suggestions=actions[:2],
        )

    def _determine_approach(self, state: dict) -> str:
        """
        Determine the coaching approach based on current state.
        """
        physical = state.get("physical", {})
        recovery = physical.get("recovery_status", "moderate")
        workouts = physical.get("workouts_this_week", 0)

        if recovery in ["exhausted", "fatigued"]:
            return "recovery_focus"
        elif workouts == 0:
            return "gentle_activation"
        elif workouts >= 5:
            return "maintenance"
        else:
            return "progressive"

    def _get_tone(self, state: dict) -> str:
        """
        Determine appropriate tone for coaching.
        """
        physical = state.get("physical", {})
        recovery = physical.get("recovery_status", "moderate")

        if recovery in ["exhausted", "fatigued"]:
            return "gentle"
        elif recovery == "fully_recovered":
            return "energetic"
        else:
            return "supportive"

    async def _generate_coaching(
        self,
        context: AgentContext,
        approach: str,
    ) -> str:
        """
        Generate coaching message using LLM or rules.
        """
        if self.client is None:
            return self._rule_based_coaching(context.user_state, approach)

        prompt = f"""
        Generate a brief coaching message (2-3 sentences) for the user.
        Coaching approach: {approach}
        
        Be specific to their situation and provide encouragement.
        """

        return await self._call_llm(prompt, context, temperature=0.7)

    def _rule_based_coaching(self, state: dict, approach: str) -> str:
        """
        Rule-based coaching when LLM unavailable.
        """
        messages = {
            "recovery_focus": (
                "Your body is telling you it needs rest. "
                "Today is about recovery, not performance. "
                "Light stretching or a short walk would be perfect."
            ),
            "gentle_activation": (
                "Let's start small today! "
                "Even a 10-minute workout counts as a win. "
                "The goal is to build momentum, not perfection."
            ),
            "maintenance": (
                "Great consistency this week! "
                "Keep up the good work while listening to your body. "
                "Quality over quantity today."
            ),
            "progressive": (
                "You're building great momentum! "
                "Ready to push a little harder today? "
                "Let's make it count."
            ),
        }
        return messages.get(approach, messages["progressive"])

    def _generate_actions(self, state: dict, approach: str) -> list[str]:
        """
        Generate specific action items.
        """
        actions_map = {
            "recovery_focus": [
                "Do 10 minutes of light stretching",
                "Hydrate well throughout the day",
                "Aim for bed 30 minutes earlier tonight",
            ],
            "gentle_activation": [
                "Start with a 10-minute walk",
                "Try a short bodyweight routine",
                "Set a reminder for tomorrow's workout",
            ],
            "maintenance": [
                "Complete your scheduled workout",
                "Focus on form and technique",
                "Log your session for tracking",
            ],
            "progressive": [
                "Challenge yourself today",
                "Try adding one extra set or rep",
                "Push your comfort zone safely",
            ],
        }
        return actions_map.get(approach, actions_map["progressive"])
