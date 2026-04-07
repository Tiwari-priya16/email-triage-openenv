from fastapi import FastAPI
from openenv.core.env_server import create_fastapi_app
from models import EmailObservation, TriageAction
from server.email_triage_environment import EmailTriageEnvironment

# Create OpenEnv app
inner_app = create_fastapi_app(
    EmailTriageEnvironment,
    TriageAction,
    EmailObservation,
)

# Mount it under /web (REQUIRED FOR HF)
app = FastAPI()
app.mount("/web", inner_app)