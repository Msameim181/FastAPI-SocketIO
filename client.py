import socketio
import asyncio
from abc import ABC, abstractmethod
from typing import Dict
import logging
import threading
import time
import sys

logger = logging.getLogger(__name__)


class IBaseSocketClient(ABC):
    @abstractmethod
    def call_backs(self):
        """Some functions register for socket to communicate by them.
        you can set event function by:
            self.sio.event
        or
            self.sio.on(<event name>)
        """
        ...

    @abstractmethod
    async def connect_to_server(self):
        """Connect to server by socketio."""
        ...

    @abstractmethod
    async def run(self):
        """Run the socket client."""
        ...

    @abstractmethod
    def start_background_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Start the background loop."""
        ...


class SocketClientConfig:
    server_url: str
    headers: Dict
    socketio_path: str = "/socket.io"
    auth: Dict = None
    logger: bool = True
    engineio_logger: bool = True
    reconnection: bool = True
    reconnection_delay: int = 3
    reconnection_attempts: int = 10

    def __init__(
        self,
        server_url: str,
        headers: Dict,
        socketio_path: str = "/socket.io",
        auth: Dict = None,
        logger: bool = True,
        engineio_logger: bool = True,
        reconnection: bool = True,
        reconnection_delay: int = 3,
        reconnection_attempts: int = 10,
    ):
        self.server_url = server_url
        self.headers = headers
        self.socketio_path = socketio_path
        self.auth = auth
        self.logger = logger
        self.engineio_logger = engineio_logger
        self.reconnection = reconnection
        self.reconnection_delay = reconnection_delay
        self.reconnection_attempts = reconnection_attempts


class BaseSocketClient(IBaseSocketClient):
    def __init__(
        self,
        config: SocketClientConfig,
        logger: logging.Logger = None,
    ):
        self.config = config
        self.sio = socketio.AsyncClient(
            handle_sigint=True,
            logger=self.config.logger,
            engineio_logger=self.config.engineio_logger,
            reconnection=self.config.reconnection,
            reconnection_delay=self.config.reconnection_delay,
            reconnection_attempts=self.config.reconnection_attempts,
        )
        self.logger = logger
        self._client_loop = asyncio.new_event_loop()

    def start_background_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        asyncio.set_event_loop(loop)
        loop.run_forever()

    @property
    def client_loop(self):
        return self._client_loop

    async def connect_to_server(self):
        try:
            await self.sio.connect(
                self.config.server_url,
                headers=self.config.headers,
                socketio_path=self.config.socketio_path,
                auth=self.config.auth,
            )
            self.logger.info("Connected to the server")
        except ConnectionError:
            self.logger.error("Connection failed.")
        await self.sio.wait()

    def call_backs(self):
        @self.sio.on("connect")
        async def connect():
            self.logger.info("Socket connected to server")

        @self.sio.on("disconnect")
        def disconnect():
            self.logger.info("Socket disconnected from server")
            self.client_loop.stop()

        @self.sio.on("message")
        async def message(data):
            self.logger.info(f"Message from server: {data}")

    async def run(self):
        self.call_backs()
        await self.connect_to_server()


if __name__ == "__main__":
    token = "test"
    config = SocketClientConfig(
        server_url="http://0.0.0.0:1234",
        headers={"Authorization": f"Bearer {token}"},
        socketio_path="/socket.io",
        auth={"token": token},
        engineio_logger=True,
    )
    base_client = BaseSocketClient(config, logger=logger)
    th = threading.Thread(
        target=base_client.start_background_loop,
        args=(base_client.client_loop,),
        daemon=True,
    )
    th.start()

    asyncio.run_coroutine_threadsafe(base_client.run(), base_client.client_loop)
    time.sleep(0.5)
    while True:
        if not base_client.sio.connected:
            logger.info("Client is not connected to the server")
            sys.exit(1)
        try:
            user_input = input('Enter a message (or "exit" to quit): ')
            if user_input.lower() == "exit":
                break
            else:
                asyncio.run_coroutine_threadsafe(
                    base_client.sio.emit("message", user_input), base_client.client_loop
                )
        except KeyboardInterrupt:
            break
    base_client.sio.disconnect()