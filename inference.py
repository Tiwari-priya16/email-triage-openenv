import os
import json
import time
from openai import OpenAI
from models import TriageAction

# === MANDATORY VARIABLES ===
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-7B-Instruct")
BENCHMARK = "email-triage-openenv"
MAX_STEPS = 20

if not HF_TOKEN:
    raise ValueError("HF_TOKEN is required.")

llm_client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

import requests

class SimpleEnvClient:
    def __init__(self, base_url="http://127.0.0.1:7860"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def reset(self, task: str = "easy"):
        resp = self.session.post(f"{self.base_url}/reset", json={"task": task})
        resp.raise_for_status()
        return resp.json()

    def step(self, action):
        if hasattr(action, "model_dump"):
            action_dict = action.model_dump()
        else:
            action_dict = dict(action)
        resp = self.session.post(f"{self.base_url}/step", json={"action": action_dict})
        resp.raise_for_status()
        return resp.json()

    def close(self):
        self.session.close()


ENV_URL = os.getenv("ENV_URL", "http://127.0.0.1:7860")
env_client = SimpleEnvClient(base_url=ENV_URL)

TASKS = ["easy", "medium", "hard"]


def get_agent_action(obs):
    if isinstance(obs, dict) and "observation" in obs:
        obs_data = obs["observation"]
    else:
        obs_data = obs

    prompt = f"""You are an expert executive assistant. Triage this email.

Email:
{json.dumps(obs_data, indent=2) if isinstance(obs_data, dict) else str(obs_data)}

Return ONLY valid JSON with exactly these fields:
{{
  "category": "<work|personal|spam|urgent|promo>",
  "priority": "<high|medium|low>",
  "action_type": "<archive|reply|forward|route_to_folder|escalate_to_human|noop>"
}}"""

    try:
        response = llm_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=200,
        )
        content = response.choices[0].message.content.strip()
        content = content.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        action_dict = json.loads(content)
        return TriageAction(**action_dict), None
    except Exception as e:
        return TriageAction(category="work", priority="medium", action_type="noop"), str(e)


all_scores = {}

for task in TASKS:
    rewards = []
    steps = 0
    success = False
    last_error = None

    try:
        obs = env_client.reset(task=task)
    except Exception as e:
        print(f"[START] task={task} env={BENCHMARK} model={MODEL_NAME}")
        print(f"[END] success=false steps=0 score=0.00 rewards=")
        all_scores[task] = 0.0
        continue

    print(f"[START] task={task} env={BENCHMARK} model={MODEL_NAME}")

    while steps < MAX_STEPS:
        action, llm_error = get_agent_action(obs)
        error_str = llm_error if llm_error else "null"

        try:
            result = env_client.step(action)
            reward = result.get("reward") or 0.0
            done = result.get("done", False)
            obs = result

            rewards.append(reward)
            steps += 1

            action_str = f"{action.category}/{action.priority}/{action.action_type}"
            print(f"[STEP] step={steps} action={action_str} reward={reward:.2f} done={str(done).lower()} error={error_str}")

            if done:
                success = True
                break
            time.sleep(0.1)

        except Exception as e:
            last_error = str(e)
            rewards.append(0.0)
            steps += 1
            action_str = f"{action.category}/{action.priority}/{action.action_type}"
            print(f"[STEP] step={steps} action={action_str} reward=0.00 done=false error={last_error}")
            break

    # Normalize score to [0, 1]: reward range is -1 to 1
    if rewards:
        avg_reward = sum(rewards) / len(rewards)
        score = round((avg_reward + 1) / 2, 2)
    else:
        score = 0.0

    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.2f} rewards={rewards_str}")

    all_scores[task] = score

env_client.close()

avg_score = sum(all_scores.values()) / len(all_scores)
print(f"\n=== FINAL RESULTS ===")
print(json.dumps(all_scores, indent=2))
print(f"Average score: {avg_score:.3f}")