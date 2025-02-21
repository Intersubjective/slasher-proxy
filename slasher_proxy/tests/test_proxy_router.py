from typing import Any, Dict

import aiohttp
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pony.orm import db_session

from slasher_proxy.avalanche.proxy_router import router
from slasher_proxy.common.model import Commitment, NodeStats, Transaction
from slasher_proxy.common.settings import SlasherRpcProxySettings, get_settings


# Dummy settings for testing.
class DummySettings(SlasherRpcProxySettings):
    # Must match what you used in conftest.
    dsn: str = "sqlite:///:memory:?cache=shared"
    rpc_url: str = "http://dummy-validator"
    node_id: str = "avalanche"


# Create the FastAPI app and include the router.
app = FastAPI()
app.include_router(router)
app.dependency_overrides[get_settings] = lambda: DummySettings()


# --- Helper mocks for aiohttp.ClientSession ---
class DummyResponse:
    def __init__(self, json_data: Dict[str, Any], status: int = 200) -> None:
        self._json_data = json_data
        self.status = status

    async def json(self) -> Dict[str, Any]:
        return self._json_data

    async def __aenter__(self) -> "DummyResponse":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        pass


class DummyClientSession:
    def __init__(
        self, json_data: Dict[str, Any] = None, *, raise_exception: bool = False
    ) -> None:
        self._json_data = json_data or {}
        self.raise_exception = raise_exception

    async def __aenter__(self) -> "DummyClientSession":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        pass

    # Changed from async def to def so that it returns a DummyResponse immediately.
    def post(self, url: str, json: Dict[str, Any]) -> DummyResponse:
        if self.raise_exception:
            raise Exception("Simulated connection error")
        return DummyResponse(self._json_data)


# Patch aiohttp.ClientSession using monkeypatch.
@pytest.fixture
def override_aiohttp(monkeypatch):
    def dummy_session_factory(*args, **kwargs):
        # By default simulate validator returning a successful response.
        dummy_json = {
            "result": {
                "txHash": "0xabcdef",
                "commitment": "0x123456",
                "txIndex": 1,
            }
        }
        return DummyClientSession(dummy_json)

    monkeypatch.setattr(aiohttp, "ClientSession", dummy_session_factory)


def test_invalid_method(override_aiohttp):
    client = TestClient(app)

    # Invalid method in the request.
    body = {"method": "eth_invalidMethod", "params": ["0xdeadbeef"]}
    response = client.post("/eth_sendRawTransaction", json=body)
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid method"


def test_invalid_params(override_aiohttp):
    client = TestClient(app)

    # Missing params field.
    body1 = {"method": "eth_sendRawTransaction"}
    response1 = client.post("/eth_sendRawTransaction", json=body1)
    assert response1.status_code == 400

    # Params is not a list.
    body2 = {"method": "eth_sendRawTransaction", "params": "not-a-list"}
    response2 = client.post("/eth_sendRawTransaction", json=body2)
    assert response2.status_code == 400

    # Params list with incorrect length.
    body3 = {"method": "eth_sendRawTransaction", "params": []}
    response3 = client.post("/eth_sendRawTransaction", json=body3)
    assert response3.status_code == 400


def test_validator_error(monkeypatch):
    # Simulate a validator error response.
    def dummy_session_factory(*args, **kwargs):
        dummy_json = {"error": {"message": "Simulated validator error"}}
        return DummyClientSession(dummy_json)

    monkeypatch.setattr(aiohttp, "ClientSession", dummy_session_factory)
    client = TestClient(app)

    body = {"method": "eth_sendRawTransaction", "params": ["0xdeadbeef"]}
    response = client.post("/eth_sendRawTransaction", json=body)
    # Expect a 400 error due to validator rejection.
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "Transaction rejected" in detail


def test_forwarding_exception(monkeypatch):
    # Simulate an exception during forwarding.
    def dummy_session_factory(*args, **kwargs):
        return DummyClientSession({}, raise_exception=True)

    monkeypatch.setattr(aiohttp, "ClientSession", dummy_session_factory)
    client = TestClient(app)

    body = {"method": "eth_sendRawTransaction", "params": ["0xdeadbeef"]}
    response = client.post("/eth_sendRawTransaction", json=body)
    assert response.status_code == 500
    detail = response.json()["detail"]
    assert "Error forwarding to validator" in detail
