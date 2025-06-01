import asyncio
import signal
import threading
from asyncio import AbstractEventLoop
import time

import uvicorn
import psycopg2
import yoyo
from starlette.middleware.cors import CORSMiddleware

from rest import router_init
from utils.config import CONFIG
from utils.logger import get_logger, get_logger_univorn
from utils.shutdown import GLOBAL_SHUTDOWN_EVENT

log = get_logger("Main")


class Main:
    def __init__(self):
        self.app = router_init.app
        self.__create_services()
        self.shutdown_event = GLOBAL_SHUTDOWN_EVENT
        self.uvicorn_start_thread: threading.Thread | None = None
        self.asyncio_thread: threading.Thread | None = None
        self.rest_server: uvicorn.Server | None = None
        self.event_loop: AbstractEventLoop | None = None

    def __create_services(self):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        # self.app.dependency_overrides[AuthService] = lambda: TestAuth() # TODO сделать по красоте, а вообще тут можно менять базовое поведение
        ...

    def start(self):
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)

        print("Checking db ...")
        self.wait_for_postgres()
        print("Execute db migrations ...")
        self.run_migrations()

        self.start_event_loop()

        self.__create_services()

        print("Starting http server ...")
        self.start_rest_server()

        print("Wait until shutdown ...")
        self.wait_until_shutdown()

    def start_event_loop(self):
        def run():
            self.event_loop.run_forever()

        self.event_loop = asyncio.new_event_loop()
        self.asyncio_thread = threading.Thread(target=run)
        self.asyncio_thread.start()
        asyncio.set_event_loop(self.event_loop)

    def wait_until_shutdown(self):
        while not self.shutdown_event.is_set():
            self.shutdown_event.wait()
        print("Shutting down servers gracefully...")
        self.rest_server.should_exit = True
        self.uvicorn_start_thread.join()

        # self.grpc_server.stop(grace=15)

        self.event_loop.call_soon_threadsafe(self.event_loop.stop)
        self.asyncio_thread.join()

        if self.event_loop.is_running():
            print("Force closing event loop...")
            self.event_loop.close()

    def start_rest_server(self):
        config = uvicorn.Config(self.app, host=CONFIG.server_host, port=CONFIG.server_rest_port, log_config=get_logger_univorn())
        self.rest_server = uvicorn.Server(config)
        self.uvicorn_start_thread = threading.Thread(target=self.rest_server.run)
        self.uvicorn_start_thread.start()

    def handle_shutdown(self, signum, frame):
        self.shutdown_event.set()

    @staticmethod
    def wait_for_postgres():
        start_time = time.time()
        while True:
            try:
                conn = psycopg2.connect(
                    host=CONFIG.db.host, port=CONFIG.db.port, user=CONFIG.db.username, password=CONFIG.db.password,
                    database=CONFIG.db.database
                )
                conn.close()
                break
            except psycopg2.OperationalError as err:
                elapsed_time = time.time() - start_time
                if elapsed_time > 60:
                    raise TimeoutError("Cannot connect to postgres DB") from err

                print("Connecting to postgres ...")
                time.sleep(1)

    @staticmethod
    def run_migrations():
        # Укажите здесь строку подключения к базе данных
        db_url = f"postgresql://{CONFIG.db.username}:{CONFIG.db.password}@{CONFIG.db.host}:{CONFIG.db.port}/{CONFIG.db.database}"

        # Получаем backend для работы с базой данных
        backend = yoyo.get_backend(db_url)

        # Указываем путь к директории с миграциями
        migrations = yoyo.read_migrations(CONFIG.db.migrations)

        # Применяем миграции
        with backend.lock():  # Захват блокировки на выполнение миграций
            backend.apply_migrations(backend.to_apply(migrations))
