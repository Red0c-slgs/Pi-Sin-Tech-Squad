import os
from dataclasses import dataclass, fields, is_dataclass

import yaml  # pyright: ignore[reportMissingModuleSource]

ROOT_PATH: str = "."


def set_root_path(path: str):
    global ROOT_PATH
    ROOT_PATH = path  # pyright: ignore[reportConstantRedefinition]


@dataclass
class GptConfig:
    url: str
    token: str
    model: str

@dataclass
class S3Config:
    url: str
    login: str
    password: str
    bucket: str

@dataclass
class PandaConfig:
    bootstrap_servers: list[str]
    security_protocol: str
    sasl_mechanism: str
    sasl_plain_username: str
    sasl_plain_password: str

@dataclass
class LoggingConfigGraylog:
    enabled: bool
    host: str
    port: int
    udp: bool


@dataclass
class LoggingConfigConsole:
    enabled: bool


@dataclass
class LoggingConfig:
    console: LoggingConfigConsole
    graylog: LoggingConfigGraylog
    app_name: str
    root_level: str
    levels: dict[str, str]


@dataclass
class RecalculateConfig:
    lower_limit: float
    upper_limit: float


@dataclass
class ConfigDB:
    host: str
    port: int
    database: str
    username: str
    password: str
    migrations: str



@dataclass
class Config:
    profile: str
    server_host: str
    server_rest_port: int
    logging: LoggingConfig
    s3: S3Config
    panda: PandaConfig
    db: ConfigDB
    recognize_service: str


class ConfigLoader:
    def __init__(self):
        self.configs = []

    def __load_if_exists(self, filename, required=False):
        if os.path.isfile(filename):
            with open(filename, "r") as f:
                yy = yaml.safe_load(f)
                if yy:
                    self.configs.append(yy)
        else:
            if required:
                raise Exception(f"Configuration file {filename} does not exists. Check the working folder.")

    def load_config(self, cls=Config) -> Config:
        profile = os.environ.get("PROFILE", "dev")

        self.__load_if_exists(f"{ROOT_PATH}/config-local.yml")
        self.__load_if_exists("/etc/cyntai-server/config.yml")
        self.__load_if_exists(f"{ROOT_PATH}/config-{profile}.yml")
        self.__load_if_exists("./config.yml", required=True)

        return self.__create_class_from_values(cls, self.__get_value, "")

    def __get_value_from_yaml(self, data: dict, key: str):
        keys = key.split(".")  # Разбиваем строку ключа на отдельные части
        value = data
        for k in keys:
            value = value.get(k)  # Проходим по каждому уровню вложенности
            if value is None:  # Если ключ не найден, возвращаем None
                return None
        return value

    def __get_value(self, vname):
        env_name = vname.upper().replace(".", "_")
        if os.getenv(env_name):
            res = os.getenv(env_name)
            if res.isdigit():
                return int(res)
            else:
                return res

        for c in self.configs:
            v = self.__get_value_from_yaml(c, vname)
            if v is not None:
                return v

    def __create_class_from_values(self, cls, get_value_func, outer_name):
        """Создает экземпляр дата-класса на основе функции получения значений, включая вложенные дата-классы."""
        kwargs = {}

        for field in fields(cls):
            # Проверяем, является ли поле вложенным дата-классом
            if is_dataclass(field.type):
                # Рекурсивно создаем вложенный дата-класс
                kwargs[field.name] = self.__create_class_from_values(field.type, get_value_func, f"{outer_name}{field.name}.")
            else:
                # Получаем значение для обычного поля
                fname = f"{outer_name}{field.name}"
                val = get_value_func(fname)
                if val is None:
                    msg = f"Field {fname} is not specified"
                    raise Exception(msg)
                kwargs[field.name] = val

        return cls(**kwargs)


CONFIG: Config = ConfigLoader().load_config(Config)
