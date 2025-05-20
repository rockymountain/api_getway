import pytest
import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient

@pytest.fixture(scope="module")
def client():
    from app.main import app
    with TestClient(app) as c:
        yield c
