from dataclasses import dataclass
from ssl import create_default_context
from threading import Thread
from typing import Callable, List

from kafka import KafkaConsumer, KafkaProducer

from utils.config import CONFIG, PandaConfig


@dataclass
class PandaMessage:
    id: str | None
    payload: dict


@dataclass
class PandaPRCResponse:
    id: str
    payload: dict


class PandaClient:
    def __init__(self, config: PandaConfig):
        self.kafka_bootstrap_args = dict(
            bootstrap_servers=config.bootstrap_servers,
            security_protocol=config.security_protocol,
            sasl_mechanism=config.sasl_mechanism,
            sasl_plain_username=config.sasl_plain_username,
            sasl_plain_password=config.sasl_plain_password,
            ssl_context=create_default_context(),
        )
        # Создаем один продюсер для отправки сообщений в любые очереди
        self.producer = KafkaProducer(**self.kafka_bootstrap_args)
        self.consumer_threads: List[Thread] = []
        self.running = False

    def start(self):
        self.running = True

    def stop(self):
        self.running = False
        for thread in self.consumer_threads:
            thread.join(timeout=5.0)
        self.producer.close()

    def consume(self, topic_name, group_name, handler: Callable):
        """
        Подписывается на получение событий из определённого топика
        :param topic_name: имя топика, например transcription-is-ready
        :param group_name: имя группы обработки, например calculate-metrics-for-loov
        :param handler: процедура обработки
        :return: None
        """
        # Создаем отдельный поток для каждого консьюмера
        thread = Thread(target=self._serve, args=(topic_name, group_name, handler))
        thread.daemon = True
        thread.start()
        self.consumer_threads.append(thread)

    def produce(self, topic_name, message):
        self.producer.send(topic_name, JSON.stringify_to_bytes(message))
        self.producer.flush()

    def _serve(self, topic_name, group_name, handler):
        consumer = KafkaConsumer(topic_name, group_id=group_name, **self.kafka_bootstrap_args)

        try:
            print(f"RPC Client is running for topic {topic_name}...")
            for msg in consumer:
                if not self.running:
                    break
                try:
                    request = JSON.parse(msg.value)
                    print(f"Received request: {request}")

                    # Выполняем обработку запроса
                    handler(request)
                except Exception as e:
                    print(f"Error processing message: {e}")
        finally:
            consumer.close()


__instance: PandaClient | None = None


def get_panda_client() -> PandaClient:
    global __instance
    if __instance is None:
        __instance = PandaClient(CONFIG.panda)
        __instance.start()
    return __instance


def start_client():
    client = get_panda_client()

    def handler(request: dict):
        print(f"I've got a message: {request}")
        client.produce("test-response", {"message": 123})

    client.consume("test-topic", "cc-analyzer", handler)

    # Блокирующее ожидание завершения (Ctrl-C)
    try:
        import signal

        signal.pause()  # Для Unix-подобных систем
    except (KeyboardInterrupt, AttributeError):
        # Для Windows или если signal.pause() недоступен
        import time

        while client.running:
            time.sleep(1)

    print("Shutting down...")
    client.stop()


if __name__ == "__main__":
    from utils.shutdown import register_shutdown_handler

    register_shutdown_handler()
    start_client()
