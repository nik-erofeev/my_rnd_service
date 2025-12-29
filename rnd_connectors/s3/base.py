import logging
import os
from abc import ABC, abstractmethod

import boto3

from rnd_connectors.s3.schemas import S3Config


class S3Base(ABC):
    def __init__(self, config: S3Config):
        self.config = config
        self.client = self.get_s3_client()
        self.bucket_name = config.bucket_name
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    def get_s3_client(self):
        """Создает и возвращает S3 клиент."""
        pass

    @abstractmethod
    def download_dir(self, s3_prefix, local_directory_path):
        """
        Загружает вложенное содержимое директории из префикса S3 в директорию контейнера.
        """
        pass

    @abstractmethod
    def upload_dir(self, local_directory_path, s3_destination_path):
        """
        Загружает вложенное содержимое директории в префикс S3.
        """
        pass


class S3Client(S3Base):
    def get_s3_client(self):
        # Определяем сессию в Boto3
        session = boto3.Session(
            aws_access_key_id=self.config.aws_access_key_id,
            aws_secret_access_key=self.config.aws_secret_access_key,
        )

        # Определяем клиента для работы с S3
        client = session.client(
            "s3", endpoint_url=self.config.endpoint_url, verify=False
        )

        return client

    # Метод для загрузки вложенного содержимого директории из префикса s3 в директорию контейнера
    def download_dir(self, s3_prefix, local_directory_path):
        self.logger.log("Определяем объекты в префиксе")
        objects_list = self.client.list_objects_v2(
            Bucket=self.bucket_name, Prefix=s3_prefix
        )["Contents"]
        self.logger.log(f"Объекты в префиксе: {objects_list}")

        for s3_object in objects_list:
            if s3_object["Key"].endswith("/"):
                folder_path = local_directory_path + "/" + s3_object["Key"]
                if not os.path.exists(folder_path):
                    self.logger.log(
                        f"Создаем директорию в локальном файловом сторадже: {folder_path}"
                    )
                    os.makedirs(folder_path)
            else:
                self.logger.log(f"Загружаем объект: {s3_object['Key']}")
                target_local_path = (
                    local_directory_path + "/" + os.path.basename(s3_object["Key"])
                )
                self.logger.log(
                    f"Конечный путь в локальном хранилище до объекта: {target_local_path}"
                )
                self.client.download_file(
                    self.bucket_name, s3_object["Key"], target_local_path
                )

    # Метод для загрузки вложенного содержимого директории в префикс s3
    def upload_dir(self, local_directory_path, s3_destination_path):
        # enumerate local files recursively
        for root, dirs, files in os.walk(local_directory_path):
            for filename in files:
                # construct the full local path
                local_path = os.path.join(root, filename)
                self.logger.log(f"Исходный путь до выгружаемого объекта: {local_path}")

                # construct the full Dropbox path
                relative_path = os.path.relpath(local_path, local_directory_path)
                s3_path = os.path.join(s3_destination_path, relative_path)
                self.logger.log(
                    f"Конечный путь до выгружаемого объекта в S3: {s3_path}"
                )

                self.client.upload_file(local_path, self.bucket_name, s3_path)
                self.logger.log("Объект загружен")
