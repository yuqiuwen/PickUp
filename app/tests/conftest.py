from collections.abc import Generator
import os

import pytest
from starlette.testclient import TestClient


def pytest_configure(config):
    os.environ["APP_ENV"] = "unittest"


from app.tests.utils.db import override_get_session
from app.config import settings
from app.database.db import get_session
from manage import app



# 重载数据库
app.dependency_overrides[get_session] = override_get_session


# Test data
PYTEST_USERNAME = 'admin'
PYTEST_PASSWORD = '123456'
PYTEST_BASE_URL = f'http://127.0.0.1{settings.FASTAPI_API_V1_PATH}'


@pytest.fixture(scope='module')
def client() -> Generator:
    with TestClient(app, base_url=PYTEST_BASE_URL) as c:
        yield c


@pytest.fixture(scope='module')
def token_headers(client: TestClient) -> dict[str, str]:
    params = {
        'username': PYTEST_USERNAME,
        'password': PYTEST_PASSWORD,
    }
    response = client.post('/auth/login/swagger', params=params)
    response.raise_for_status()
    token_type = response.json()['token_type']
    access_token = response.json()['access_token']
    headers = {'Authorization': f'{token_type} {access_token}'}
    return headers