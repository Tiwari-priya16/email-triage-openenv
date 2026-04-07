# from fastapi import FastAPI
from openenv.core.env_server import create_fastapi_app
from models import EmailObservation, TriageAction
from server.email_triage_environment import EmailTriageEnvironment

# Inner OpenEnv app
inner_app = create_fastapi_app(
    EmailTriageEnvironment,
    TriageAction,
    EmailObservation,
)

# # Main app
# app = FastAPI()

# # ROOT FIX (IMPORTANT)
# @app.get("/")
# def root():
#     return {"message": "API is running. Use /web endpoints."}

# Mount API
# app.mount("/web", inner_app)