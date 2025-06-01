import os
import re
from pathlib import Path

import boto3
from botocore.config import Config

from utils.config import S3Config


class S3:
    def __init__(self, s3_config: S3Config):
        self.s3_config = s3_config
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=s3_config.url,
            aws_access_key_id=s3_config.login,
            aws_secret_access_key=s3_config.password,
            config=Config(signature_version="s3v4"),
        )

    def get_local_file(self, s3_file, local_file=None) -> str:
        if not local_file:
            basename = os.path.basename(s3_file)
            # date = datetime_str(datetime.datetime.now()) TODO
            date = "52354/4324/4234"
            ext = Path(s3_file).suffix
            local_file = f"/tmp/s3-{basename}.{date}{ext}"
        else:
            local_file = os.path.join(".", local_file)

        if os.path.exists(local_file):
            return local_file

        os.makedirs(os.path.dirname(local_file), exist_ok=True)

        s3_response = self.s3_client.get_object(Bucket=self.s3_config.bucket, Key=s3_file)

        with open(local_file, "wb") as ff:
            ff.write(s3_response["Body"].read())

        return local_file

    def ls(self, folder, mask=None) -> list[str]:
        """
        Список объектов в S3 на одном уровне, аналог команды ls.
        Сначала возвращает папки (с `/` на конце), затем файлы.

        :param folder: Строка в формате "bucket_name/prefix" (например, "my-bucket/path/to/folder/")
                       Если нет префикса, то указывайте просто "bucket_name/".
        :return: Список объектов (папки с `/` на конце и файлы).
        """
        # Разделяем bucket и prefix
        if "/" not in folder:
            raise ValueError("Путь должен быть в формате 'bucket_name/prefix/' или 'bucket_name/'")

        prefix = folder
        if prefix.startswith("/"):
            prefix = prefix[1:]
        if not prefix.endswith("/"):
            prefix += "/"

        folders = []
        files = []

        # Используем пагинацию для обработки всех объектов
        paginator = self.s3_client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.s3_config.bucket, Prefix=prefix, Delimiter="/"):
            # Добавляем папки
            if "CommonPrefixes" in page:
                folders.extend(cp["Prefix"].replace(prefix, "", 1) for cp in page["CommonPrefixes"])
            # Добавляем файлы
            if "Contents" in page:
                files.extend(
                    obj["Key"].replace(prefix, "", 1)
                    for obj in page["Contents"]
                    if obj["Key"] != prefix  # Исключаем сам префикс как объект
                )

        # Возвращаем папки и файлы
        ret = sorted(folders) + sorted(files)
        if mask:
            ret = [x for x in ret if re.match(mask, x)]

        return ret

    def delete(self, filename: str):
        self.s3_client.delete_object(Bucket=self.s3_config.bucket, Key=filename)

    def exists(self, filename: str) -> bool:
        try:
            self.s3_client.head_object(Bucket=self.s3_config.bucket, Key=filename)
            return True
        except self.s3_client.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise

    def get_file_content_as_str(self, filename: str) -> str:
        try:
            s3_response = self.s3_client.get_object(Bucket=self.s3_config.bucket, Key=filename)
            content = s3_response["Body"].read().decode("utf-8")
            return content
        except self.s3_client.exceptions.ClientError as err:
            raise FileNotFoundError(f"File {filename} not found in bucket {self.s3_config.bucket}") from err

    def write_file(self, filename: str, content: str):
        try:
            self.s3_client.put_object(Bucket=self.s3_config.bucket, Key=filename, Body=content.encode("utf-8"))
        except self.s3_client.exceptions.ClientError as e:
            raise RuntimeError(f"Failed to write file {filename} to bucket {self.s3_config.bucket}: {e}") from e

    def upload_file(self, local_file, s3_file) -> str:
        try:
            self.s3_client.upload_file(local_file, self.s3_config.bucket, s3_file)
            return f"{self.s3_config.url}/{self.s3_config.bucket}/{s3_file}"
        except Exception as e:
            return f"Ошибка при загрузке {s3_file}: {str(e)}"
