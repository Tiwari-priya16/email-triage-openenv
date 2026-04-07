from openenv.core.env_server import create_fastapi_app
from models import EmailObservation, TriageAction
from server.email_triage_environment import EmailTriageEnvironment

app = create_fastapi_app(
    EmailTriageEnvironment,
    TriageAction,
    EmailObservation,
)