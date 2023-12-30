import socketio
import uvicorn
from fastapi import FastAPI
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class IBaseSocketServer(ABC):
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
    def run_server(self):
        """
        Run socket server:
        - create app
        - attach app to socket
        - register call back functions (event functions)
        - run the application and set host and port to it
        """
        ...

class SocketServerConfig:
    host: str
    port: int
    log_level: str = "info"
    cors_allowed_origins: str = "*"
    socketio_path: str = "/socket.io"
    logger: bool = True
    always_connect: bool = True
    engineio_logger: bool = True
    server_workers: int = None
    reload: bool = False

    def __init__(
        self,
        host: str,
        port: int = 8000,
        log_level: str = "info",
        cors_allowed_origins: str = "*",
        socketio_path: str = "/socket.io",
        logger: bool = True,
        always_connect: bool = True,
        engineio_logger: bool = True,
        server_workers: int = None,
    ):
        self.host = host
        self.port = port
        self.log_level = log_level
        self.cors_allowed_origins = cors_allowed_origins
        self.socketio_path = socketio_path
        self.logger = logger
        self.always_connect = always_connect
        self.engineio_logger = engineio_logger
        self.server_workers = server_workers

class BaseSocketServer(IBaseSocketServer):
    def __init__(
        self,
        config: SocketServerConfig,
        async_mode: str = "asgi",
        cors_allowed_origins: str = "*",
        logger: logging.Logger = None,
    ):
        self.config = config
        self.fastapi_app = FastAPI()
        self.api_route()
        self.sio = socketio.AsyncServer(
            async_mode="asgi", 
            cors_allowed_origins=self.config.cors_allowed_origins, always_connect=self.config.always_connect,
            logger=self.config.logger, engineio_logger=self.config.engineio_logger
        )
        self.app = socketio.ASGIApp(
            self.sio, self.fastapi_app, socketio_path=self.config.socketio_path
        )
        self.logger = logger

    def run_server(self):
        self.call_backs()
        uvicorn.run(
            self.app,
            host=self.config.host,
            port=self.config.port,
            log_level=self.config.log_level,
            workers=self.config.server_workers, 
        )

    def api_route(self):
        @self.fastapi_app.get("/")
        def home():
            return {"message": "Hello World"}

        @self.fastapi_app.get("/send/{room_id}/{message}")
        async def send_message(room_id: str, message: str):
            self.logger.info(f"[API] Send message to {room_id}: {message}")
            await self.send_message(room_id, message)
            return {"message": "OK"}

    def call_backs(self):
        @self.sio.on("connect")
        async def connect(sid, environ, auth):
            self.logger.info(environ)
            self.logger.info(f"Socket connected with ID: {sid}")
            if auth:
                self.logger.info(f"Auth: {auth}")
            else:
                self.logger.info("No Auth")
                # @TODO: add auth to socket
            await self.sio.emit("connected", room=sid)

        @self.sio.on("disconnect")
        def disconnect(sid):
            self.logger.info(f"Socket disconnected with ID: {sid}")

        @self.sio.on("join")
        async def join(sid, room):
            await self.sio.enter_room(sid, room)
            self.logger.info(f"Client {sid} joined room {room}, {self.sio.rooms(sid)}")

        @self.sio.on("leave")
        async def leave(sid, room):
            await self.sio.leave_room(sid, room)
            self.logger.info(f"Client {sid} left room {room}")

        @self.sio.on("message")
        async def message(sid, data):
            self.logger.info(f"Message from {sid}: {data}")
            self.logger.info("Sending message to somewhere")

    # send a outside message to client with room id
    async def send_message(self, room_id: str, message: str):
        self.logger.info(f"Send message to {room_id}: {message}")
        await self.sio.emit("message", message, room=room_id)


if __name__ == "__main__":
    config = SocketServerConfig(
        host="0.0.0.0", port=1234, log_level="info",
        logger=False, engineio_logger=False
    )
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler())
    server = BaseSocketServer(config=config, logger=logger)
    server.run_server()
