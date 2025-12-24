import os

from app import create_app


app_env = os.getenv("APP_ENV", "development")

app = create_app(app_env)
