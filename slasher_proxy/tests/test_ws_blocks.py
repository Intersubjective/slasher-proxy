import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from websockets.exceptions import ConnectionClosed

from slasher_proxy.avalanche.ws_blocks import WebSocketListener

message_content = {
    "params": {
        "result": {"number": "0x1a", "hash": "0x123456", "parentHash": "0xabcdef"}
    }
}

valid_message = json.dumps(message_content)


@pytest.mark.asyncio
async def test_process_messages_valid_block():
    mock_websocket = AsyncMock()
    mock_parse_and_save = MagicMock()
    mock_check_block = MagicMock()

    listener = WebSocketListener(
        url="wss://test.com:443",
        parse_and_save_func=mock_parse_and_save,
        check_block_func=mock_check_block,
    )

    mock_websocket.recv.side_effect = [valid_message, ConnectionClosed(None, None)]

    await listener._WebSocketListener__process_messages(mock_websocket, "test_node_id")  # type: ignore[attr-defined]

    mock_parse_and_save.assert_called_once_with(
        message_content["params"], "test_node_id"
    )
    mock_check_block.assert_called_once_with(26)
