import os
from pathlib import Path

from load_env import load_env


app_env = load_env()

from app.main import create_app  # noqa

app = create_app(app_env)
