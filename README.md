---
title: Email Triage Environment Server
emoji: 📯
colorFrom: blue
colorTo: red
sdk: docker
pinned: false
app_port: 7860
base_path: /web
tags:
  - openenv
---

# Email Triage OpenEnv — Meta PyTorch Hackathon

An enterprise-grade email triage reinforcement learning environment built for the **Meta PyTorch OpenEnv Hackathon Round 1 (April 2026)**.

A realistic RL environment where an AI agent learns to triage emails — categorizing, prioritizing, and routing them — using the standard OpenEnv `step()` / `reset()` / `state()` API.

---

## Overview

Modern professionals receive hundreds of emails daily. This environment simulates an enterprise inbox where an AI agent must triage emails efficiently under an attention budget constraint. The agent learns to:

- Categorize emails (work, personal, spam, urgent, promo)
- Assign priority (high, medium, low)
- Choose the right action (reply, archive, forward, escalate, etc.)

---

## Tasks

| Task | Description | Emails | Attention Budget |
|------|-------------|--------|-----------------|
| `easy` | Single non-threaded emails | 3 | 10 |
| `medium` | Email threads requiring context | 2 | 10 |
| `hard` | Full inbox with mixed types | 7 | 20 |

---

## Baseline Scores

| Task | Score |
|------|-------|
| Easy | ~0.93 |
| Medium | ~0.90 |
| Hard | ~0.81 |
| **Average** | **~0.88** |

---

## Action Space

```python
class TriageAction(BaseModel):
    category: Literal["work", "personal", "spam", "urgent", "promo"]
    priority: Literal["high", "medium", "low"]
    action_type: Literal["archive", "reply", "forward", "route_to_folder", "escalate_to_human", "noop"]
    folder: Optional[str] = None
    reply_draft: Optional[str] = None
    forward_to: Optional[str] = None
```

## Observation Space

```python
class EmailObservation(BaseModel):
    email_id: str
    subject: str
    sender: str
    body_snippet: str
    timestamp: str
    thread_id: Optional[str]
    sender_reputation: float      # 0.0 - 1.0
    is_time_sensitive: bool
    reward: float
    done: bool
```

---

## Reward Function

The reward is calculated based on how well the agent's action matches the ground truth:

| Condition | Reward |
|-----------|--------|
| Correct category | +0.35 |
| Wrong category | -0.25 |
| Correct priority | +0.25 |
| Correct action type | +0.40 |
| Escalate high priority (partial) | +0.20 |
| Thread-aware reply/forward | +0.15 |
| Archive time-sensitive email | -0.45 |
| Low priority on high priority email | -0.30 |

Scores are normalized to **[0, 1]** range.

---

## Setup & Installation

### Requirements

- Python 3.10+
- HuggingFace account with API token

### Install

```bash
git clone https://github.com/PARIKSHIT-hub/email-triage-openenv
cd email-triage-openenv
pip install -r requirements.txt
```

### Run the Server

```bash
uvicorn server.app:app --host 0.0.0.0 --port 8000
```

### Run the Inference Agent

```bash
export HF_TOKEN=your_huggingface_token
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=Qwen/Qwen2.5-7B-Instruct
python inference.py
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HF_TOKEN` | HuggingFace API token | Required |
| `API_BASE_URL` | LLM API endpoint | `https://router.huggingface.co/v1` |
| `MODEL_NAME` | LLM model name | `Qwen/Qwen2.5-7B-Instruct` |
| `ENV_URL` | Environment server URL | `http://127.0.0.1:8000` |

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/reset` | POST | Start a new episode |
| `/step` | POST | Execute an action |
| `/state` | GET | Get current environment state |
| `/health` | GET | Health check |
| `/schema` | GET | Get action/observation schemas |
| `/docs` | GET | Swagger UI |

---

## Project Structure

```
email-triage-openenv/
├── inference.py                  # Baseline LLM agent
├── models.py                     # Pydantic data models
├── client.py                     # Environment client
├── __init__.py                   # Package init
├── openenv.yaml                  # OpenEnv config
├── Dockerfile                    # Docker deployment
├── requirements.txt              # Dependencies
├── pyproject.toml               # Project config
└── server/
    ├── app.py                    # FastAPI app
    ├── email_triage_environment.py  # Core environment logic
    └── __init__.py
```

---

## Docker

```bash
docker build -t email-triage-env .
docker run -p 8000:8000 \
  -e HF_TOKEN=your_token \
  -e API_BASE_URL=https://router.huggingface.co/v1 \
  -e MODEL_NAME=Qwen/Qwen2.5-7B-Instruct \
  email-triage-env
```

---

## Built For

**Meta PyTorch OpenEnv Hackathon — Round 1, April 2026**

Team: RLForgeSync

| Role | Name | Email |
|------|------|-------|
| Team Lead | Priya Tiwari | priyatiwari.dev16@gmail.com |
| Member | Prikshit Deshwal | prikshitdeshwal1@gmail.com |