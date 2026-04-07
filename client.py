# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.

"""Email Triage Environment Client."""

from typing import Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

from models import TriageAction, EmailObservation


class EmailTriageEnv(
    EnvClient[TriageAction, EmailObservation, State]
):
    """
    Client for the Email Triage Environment.
    """

    def _step_payload(self, action: TriageAction) -> Dict:
        """Convert TriageAction to JSON payload for step message."""
        return action.model_dump()

    def _parse_result(self, payload: Dict) -> StepResult[EmailObservation]:
        """Parse server response into StepResult."""
        
        obs_data = payload.get("observation", {})

        observation = EmailObservation(
            email_id=obs_data.get("email_id", ""),
            subject=obs_data.get("subject", ""),
            sender=obs_data.get("sender", ""),
            body_snippet=obs_data.get("body_snippet", ""),
            timestamp=obs_data.get("timestamp", ""),
            thread_id=obs_data.get("thread_id"),
            sender_reputation=obs_data.get("sender_reputation", 0.5),
            is_time_sensitive=obs_data.get("is_time_sensitive", False),
            reward=obs_data.get("reward", 0.0),
            done=obs_data.get("done", False),
        )

        return StepResult(
            observation=observation,
            reward=payload.get("reward", 0.0),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> State:
        """Parse server response into State object."""
        
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
        )