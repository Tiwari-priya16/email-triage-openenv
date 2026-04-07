import sys
import os

# Add both root and server/ to path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(ROOT, "server")
sys.path.insert(0, ROOT)
sys.path.insert(0, SERVER)

from fastapi import FastAPI
from openenv.core.env_server import create_fastapi_app
from models import EmailObservation, TriageAction
from email_triage_environment import EmailTriageEnvironment

# 👉 create inner app
inner_app = create_fastapi_app(
    EmailTriageEnvironment,
    TriageAction,
    EmailObservation,
)

# 👉 mount it on /web (THIS IS THE FIX)
app = FastAPI()
app.mount("/web", inner_app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)