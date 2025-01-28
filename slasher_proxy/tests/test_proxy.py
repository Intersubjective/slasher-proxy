from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from pydantic import PostgresDsn

from slasher_proxy.asgi import create_slasher_app
from slasher_proxy.common import T_STATUS_SUBMITTED
from slasher_proxy.common.settings import SlasherRpcProxySettings, set_settings


@pytest.fixture
def client(mock_settings):
    set_settings(mock_settings)
    return TestClient(create_slasher_app())


@pytest.fixture
def mock_settings():
    return SlasherRpcProxySettings(
        dsn=PostgresDsn("postgresql://user:password@localhost:5432/testdb"),
        rpc_url="http://mock-avalanche-rpc.localhost:12345",
        log_level="INFO",
        port=5500,
        host="0.0.0.0",
        blocks_channel="test_channel",
        network_name="test_network",
    )


def test_handle_send_raw_transaction_returns_avalanche_response(mock_settings, client):
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"result": "0xabcdef1234567890"}
        mock_post.return_value.__aenter__.return_value = mock_response

        with patch("slasher_proxy.avalanche.proxy_router.db_session"):
            with patch("slasher_proxy.avalanche.proxy_router.Transaction"):
                with patch(
                    "slasher_proxy.avalanche.proxy_router.get_settings",
                    return_value=mock_settings,
                ):
                    request_body = {
                        "method": "eth_sendRawTransaction",
                        "params": ["0xf86c0185052ec0..."],
                    }
                    response = client.post("/eth_sendRawTransaction", json=request_body)

                    if response.status_code == 500:
                        print("Error details:", response.json())

                    assert response.status_code == 200, (
                        f"Unexpected status code: {response.status_code}. "
                        + f"Response: {response.json()}"
                    )
                    assert response.json() == {"result": "0xabcdef1234567890"}


def test_handle_send_raw_transaction_saves_to_db(mock_settings, client):
    with patch("aiohttp.ClientSession.post") as mock_post:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"result": "0xabcdef1234567890"}
        mock_post.return_value.__aenter__.return_value = mock_response

        with patch(
            "slasher_proxy.avalanche.proxy_router.db_session"
        ) as mock_db_session:
            with patch(
                "slasher_proxy.avalanche.proxy_router.Transaction"
            ) as mock_transaction:
                with patch(
                    "slasher_proxy.avalanche.proxy_router.get_settings",
                    return_value=mock_settings,
                ):
                    request_body = {
                        "method": "eth_sendRawTransaction",
                        "params": ["0xf86c0185052ec0..."],
                    }
                    response = client.post("/eth_sendRawTransaction", json=request_body)

                    assert response.status_code == 200
                    assert response.json() == {"result": "0xabcdef1234567890"}

                    mock_transaction.assert_called_once_with(
                        hash=b"\xab\xcd\xef\x12\x34\x56\x78\x90",
                        status=T_STATUS_SUBMITTED,
                        raw_content=b'{"result": "0xabcdef1234567890"}',
                    )
                    mock_db_session.__enter__.assert_called_once()
                    mock_db_session.__exit__.assert_called_once()
