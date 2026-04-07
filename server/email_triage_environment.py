import random
from typing import Optional, Dict, Any, ClassVar
from datetime import datetime
from openenv.core.env_server import Environment

from models import EmailObservation, TriageAction, EnvironmentState

EMAIL_DATASET = [
    {"id": "e001", "subject": "Q3 Financial Report - Review Needed", "sender": "ceo@company.com", "body": "Please review the Q3 numbers before tomorrow's board meeting.", "category": "urgent", "priority": "high", "ground_action": "reply", "thread_id": None, "reputation": 0.95, "time_sensitive": True},
    {"id": "e002", "subject": "Team Offsite Planning", "sender": "hr@company.com", "body": "Suggestions for the upcoming team offsite are welcome.", "category": "personal", "priority": "medium", "ground_action": "archive", "thread_id": None, "reputation": 0.75, "time_sensitive": False},
    {"id": "e003", "subject": "Special Offer - 70% Off Software", "sender": "marketing@external.com", "body": "Limited time deal for your business.", "category": "promo", "priority": "low", "ground_action": "archive", "thread_id": None, "reputation": 0.3, "time_sensitive": False},
    {"id": "m001", "subject": "Project Alpha - Client Feedback", "sender": "pm@company.com", "body": "Client has some changes. See attached.", "category": "work", "priority": "high", "ground_action": "reply", "thread_id": "alpha-2026", "reputation": 0.85, "time_sensitive": True},
    {"id": "m002", "subject": "Re: Project Alpha - Client Feedback", "sender": "client@partner.com", "body": "Can we discuss the timeline adjustment?", "category": "work", "priority": "high", "ground_action": "reply", "thread_id": "alpha-2026", "reputation": 0.9, "time_sensitive": True},
    {"id": "h001", "subject": "Board Presentation Due in 2 Hours", "sender": "chairman@company.com", "body": "Final slides must be approved now.", "category": "urgent", "priority": "high", "ground_action": "escalate_to_human", "thread_id": None, "reputation": 0.98, "time_sensitive": True},
    {"id": "h002", "subject": "Weekly Company Newsletter", "sender": "internal-news@company.com", "body": "Read the latest updates from all departments.", "category": "promo", "priority": "low", "ground_action": "archive", "thread_id": None, "reputation": 0.6, "time_sensitive": False},
]

# FIX: class-level state so all requests share the same environment instance
_state: Optional[EnvironmentState] = None
_emails: list = []
_index: int = 0
_grader_scores: Dict[str, float] = {"easy": 0.0, "medium": 0.0, "hard": 0.0}


class EmailTriageEnvironment(Environment):
    def __init__(self):
        super().__init__()

    def reset(self, task: str = "easy", **kwargs) -> EmailObservation:
        global _state, _emails, _index, _grader_scores

        _state = EnvironmentState(task_name=task)
        _grader_scores[task] = 0.0

        if task == "easy":
            _emails = random.sample([e for e in EMAIL_DATASET if not e.get("thread_id")], 3)
            _state.attention_budget_remaining = 10
        elif task == "medium":
            _emails = [e for e in EMAIL_DATASET if e.get("thread_id")]
            _state.attention_budget_remaining = 10
        else:  # hard
            _emails = random.sample(EMAIL_DATASET, min(7, len(EMAIL_DATASET)))
            _state.attention_budget_remaining = 20

        _index = 0
        return self._get_observation(reward=0.0)

    def step(self, action: TriageAction) -> EmailObservation:
        global _state, _emails, _index, _grader_scores

        if not _state or _index >= len(_emails):
            return self._get_observation(reward=0.0, force_done=True)

        email = _emails[_index]
        reward = self._calculate_reward(email, action)

        _state.step_count += 1
        _state.emails_processed += 1
        _state.processed_emails.append(email["id"])
        _state.attention_budget_remaining = max(0, _state.attention_budget_remaining - 1)

        _index += 1
        budget_done = _state.attention_budget_remaining <= 0
        self._update_grader(email, action, reward)

        return self._get_observation(reward=reward, force_done=budget_done)

    def _get_observation(self, reward: float = 0.0, force_done: bool = False) -> EmailObservation:
        global _emails, _index

        if force_done or _index >= len(_emails):
          return EmailObservation(
        email_id="episode_complete",
        subject="",
        sender="",
        body_snippet="",
        timestamp=datetime.now().isoformat(),
        thread_id=None,
        sender_reputation=0.0,
        is_time_sensitive=False,
        reward=reward,
        done=True,
        )

        email = _emails[_index]
        return EmailObservation(
            email_id=email["id"],
            subject=email["subject"],
            sender=email["sender"],
            body_snippet=email["body"][:180],
            timestamp=datetime.now().isoformat(),
            thread_id=email.get("thread_id"),
            sender_reputation=email.get("reputation", 0.5),
            is_time_sensitive=email.get("time_sensitive", False),
            reward=reward,
            done=False,
        )

    def _calculate_reward(self, email: dict, action: TriageAction) -> float:
        reward = 0.0
        if action.category == email.get("category"):
            reward += 0.35
        else:
            reward -= 0.25
        if action.priority == email.get("priority"):
            reward += 0.25
        if action.action_type == email.get("ground_action"):
            reward += 0.4
        elif action.action_type == "escalate_to_human" and email.get("priority") == "high":
            reward += 0.2
        if email.get("thread_id") and action.action_type in ["reply", "forward"]:
            reward += 0.15
        if email.get("time_sensitive") and action.action_type == "archive":
            reward -= 0.45
        if action.priority == "low" and email.get("priority") == "high":
            reward -= 0.3
        return max(-1.0, min(1.0, reward))

    def _update_grader(self, email: dict, action: TriageAction, reward: float):
        global _state, _grader_scores
        task = _state.task_name
        match_score = (
            1.0 if (
                action.category == email.get("category")
                and action.priority == email.get("priority")
                and action.action_type == email.get("ground_action")
            )
            else 0.6 if reward > 0.4
            else 0.2
        )
        _grader_scores[task] = 0.7 * _grader_scores.get(task, 0.0) + 0.3 * match_score

    def state(self):
        return _state or EnvironmentState()

    def get_task_score(self, task: str) -> float:
        return round(_grader_scores.get(task, 0.0), 2)