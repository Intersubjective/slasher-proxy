from typing import Any, Callable, Dict, Optional

import asyncio
import json
from urllib.parse import urlparse

import aiohttp
import websockets
from websockets.exceptions import ConnectionClosed

from slasher_proxy.common.log import LOGGER


async def get_node_id(rpc_url: str) -> Optional[str]:
    """Fetch the Avalanche Node ID asynchronously."""
    payload = {"jsonrpc": "2.0", "id": 1, "method": "info.getNodeID", "params": {}}

    async with aiohttp.ClientSession() as session:
        async with session.post(rpc_url, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                node_id = data.get("result", {}).get("nodeID", "Unknown")
                LOGGER.info(f"Node ID: {node_id}")
                return str(node_id)
            else:
                error_text = await response.text()
                LOGGER.error(f"Failed to fetch Node ID: {error_text}")
                return None


class WebSocketListener:
    def __init__(
        self,
        url: str,
        parse_and_save_func: Callable[[Dict[str, Any], str], Dict[str, Any]],
        check_block_func: Callable[[int], None],
    ):
        self.url = url
        self.parse_and_save_func = parse_and_save_func
        self.check_block_func = check_block_func

    async def listen(self) -> None:
        while True:
            try:
                await self.__handle_websocket_connection()
            except Exception as e:
                LOGGER.error(f"Error in WebSocket connection: {e}")
                LOGGER.info("Reconnecting in 5 seconds...")
                await asyncio.sleep(5)

    async def __handle_websocket_connection(self) -> None:
        node_id = await self.__get_node_id()

        async with websockets.connect(self.url) as websocket:
            LOGGER.info(f"Connected to WebSocket at {self.url}")
            await self.__subscribe_to_new_heads(websocket)
            await self.__process_messages(websocket, node_id)

    async def __get_node_id(self) -> str:
        parsed_url = urlparse(self.url)
        hostname = parsed_url.hostname
        port = parsed_url.port or (443 if parsed_url.scheme == "wss" else 80)
        rpc_scheme = "https" if parsed_url.scheme == "wss" else "http"
        rpc_url = f"{rpc_scheme}://{hostname}:{port}/ext/info"
        node_id = await get_node_id(rpc_url)
        if node_id is None:
            raise ValueError("NodeID is not available.")
        return node_id

    @staticmethod
    async def __subscribe_to_new_heads(websocket: Any) -> None:
        subscribe_msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_subscribe",
            "params": ["newHeads"],
        }
        await websocket.send(json.dumps(subscribe_msg))

    async def __process_messages(self, websocket: Any, node_id: str) -> None:
        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)
                if "params" in data and "result" in data["params"]:
                    block_number = int(data["params"]["result"]["number"], 16)
                    LOGGER.info(f"New block received: {block_number}")
                    self.parse_and_save_func(data["params"], node_id)
                    self.check_block_func(block_number)
                else:
                    LOGGER.info(f"Received message: {json.dumps(data, indent=2)}")
            except ConnectionClosed:
                LOGGER.error("WebSocket connection closed. Reconnecting...")
                break
