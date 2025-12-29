"""
Установить ModelRepo надо как пакет. Скачать .whl файл можно тут


"""

import logging
import os
import uuid
from pathlib import Path

from rnd_connectors.mr.exceptions import ModelRepoException
from rnd_connectors.mr.schemas import MRConfig, DownloadBatchResult

logger = logging.getLogger(__name__)


class ModelRepoHandler:
    """
    Класс для работы с библиотекой model_repo.

    """

    def __init__(self, config: MRConfig):
        os.environ["rest_base_url_mr"] = (
            config.rest_base_url_mr
        )  # приходится переносить импорт сюда,
        # тк надо задать эту переменную окружения перед тем, как мы импортируем model_repo.
        # Значение по умолчанию из pydantic модели не передаются в os как переменные окружения.
        from model_repo import ModelRepo

        self.repo_client = ModelRepo()
        self.repo_client.authorize(config.email, config.password)
        self.batch_size = config.batch_size

    @staticmethod
    def filter_none_args(**kwargs) -> dict:
        return {k: v for k, v in kwargs.items() if v is not None}

    @staticmethod
    def create_uuid4() -> str:
        return str(uuid.uuid4())

    def create_repo(
        self,
        version_id: str | None = None,
        model_name: str | None = None,
        model_id: str | None = None,
        descr: str | None = None,
    ):
        """
        model_name - Наименование модели.
        (глобальное банковское наименование модели,
        например "Модель рассчета кредитного рейтинга для ИП 40+ .........").
        Является ключом для репозиториев семейства одной модели.
        один и ТОЛЬКО ОДИН из двух параметров "model-name"
        или "model-id" обязательно должен быть задан.
        model_id - Примечание: один и ТОЛЬКО ОДИН из двух параметров
        "model-name" или "model-id" обязательно должен быть задан.
        Глобальный  идентифкатор модели в формате UUID-4.
        Также является ключом для репозиториев семейства одной модели.
        Связка параметров "model-name" и "model-id" 1-к-1
        version_id - Идентификатор версии модели в формате UUID-4.
        Может быть получен при регистрации модели в СУМ,
        может быть задан процессом АвтоМЛ или DataScientist
        через библиотеку 1655_17 при вызове из Jupyter.
        Должен быть уникальным, является primary-ключом созданного репозитория
        descr - Описание версии модели
        """
        if not version_id:
            version_id = self.create_uuid4()
            logger.info("Сгенерирован uuid4 для репозитория : %s", version_id)
        filtered_args = self.filter_none_args(
            model_name=model_name, model_id=model_id, version_id=version_id, descr=descr
        )
        res = self.repo_client.create_model_repo(**filtered_args)
        logger.info("Результат создания репо: %s", res)
        return res

    def search_repo(
        self,
        version_id: str | None = None,
        model_name: str | None = None,
        model_id: str | None = None,
        descr: str | None = None,
    ):
        """
        Как происходит поиск по каждому параметру:

        model_id - Полное совпадение идентификатора
        version_id - Полное совпадение идентификатора
        descr  - LIKE %input descr%. Cовпадение подстроки  по правилу SQL LIKE
        model_name - Cовпадение подстроки  по правилу SQL LIKE
        """
        filtered_args = self.filter_none_args(
            model_name=model_name, model_id=model_id, version_id=version_id, descr=descr
        )
        res = self.repo_client.get_repo_by_params(**filtered_args)
        logger.info("Результат поиска репо: %s", res)
        return res

    def upload_files(
        self,
        version_id: str,
        files: list[str] | None = None,
        folders: list[str] | None = None,
    ):
        """
        version_id - Идентификатор версии модели
        files - Передаваемые для загрузки файлы
        folders: Список папок, которые нужно загрузить в репозиторий
        """
        res = self.repo_client.upload_files_to_repo(version_id=version_id, files=files, folders=folders)
        logger.info("Результат загрузки файлов в репо: %s", res)
        return res

    def get_repo_files(
        self,
        version_id: str,
        file_mask: list[str] | None = None,
        with_details: bool = False,
    ):
        """
        version_id - Идентификатор версии модели
        files - Непустой список с заданными файловыми масками с подстановкой ? и *
        with_details - Требование передавать расширенную информацию о файлах со списком версий
        """
        res = self.repo_client.get_repo_files_list(
            version_id=version_id, file_mask=file_mask, with_details=with_details
        )
        logger.info("Результат получения файлов с репо: %s", res)
        return res

    def clone_repo(self, version_id: str, destination_folder: str):
        """
        version_id - Идентификатор версии модели
        destination_folder -
        """
        res = self.repo_client.clone(version_id=version_id, destination=destination_folder)
        logger.info("Результат клонирования репо: %s", res)
        return res

    def delete_files(self, version_id: str, files: list[str], confirm: bool):
        """
        version_id - Идентификатор версии модели
        files - Список файлов для удаления. Обязательный не пустой список.
        Содержит строки вида "filename.extension" - полное наименование файла.
        Примечание: если какого-то из указанных в списке файлов нет в репозитории,
        то такой файл игнорируется. Удаляются только фактически присутствующие
        confirm - Обязательное подтверждение
        """
        res = self.repo_client.delete_files_in_repo(version_id=version_id, files=files, confirm=confirm)
        logger.info("Результат удаления файлов с репо: %s", res)
        return res

    def delete_repo(self, version_id: str):
        """
        version_id - Идентификатор версии модели
        """
        res = self.repo_client.delete_repo(version_id=version_id)
        logger.info("Результат удаления репо: %s", res)
        return res

    def _download_file_batch(
            self,
            version_id: str,
            batch: list[str],
            batch_num: int,
            total_batches: int,
            destination_folder: str,
    ) -> DownloadBatchResult:
        """Скачивает один батч файлов."""
        logger.info(f"📦 Скачивание батча {batch_num}/{total_batches} ({len(batch)} файлов)")

        try:
            res = self.repo_client.download_files_from_repo(
                version_id=version_id,
                objects=batch,
                destination=destination_folder,
            )

            if res and "error" in res:
                logger.error(f"❌ Ошибка в батче {batch_num}: {res.get('error')}")
                return DownloadBatchResult(results=[], success=False)

            downloaded_file_names = [Path(f).name for f in batch]
            logger.info(f"✅ Батч {batch_num}/{total_batches} успешно обработан")
            return DownloadBatchResult(results=downloaded_file_names, success=True)

        except Exception as batch_error:
            logger.error(f"❌ Ошибка в батче {batch_num}: {batch_error}")
            return DownloadBatchResult(results=[], success=False)

    def download_files(
        self,
        version_id: str,
        objects: list[str],
        destination_folder: str,
    ) -> list[str]:
        """
        version_id - Идентификатор версии модели
        objects - Список запрашиваемых файлов. Обязательный не пустой список.
        Допускается включать в список запрос на скачиванеи файла в двух форматах:
        1) "filename.extension" - текстовое значение, содержащее полное наименование файла,
        в таком случае предоставляется последняя версия указанного файла
        2) {"filename": "filename.extension", "version": "v2"}
        в формате словаря с указанием имени файла и номера версии.
        Примечание №1: если репозиторий не содержит файл с указанным именем,
        то запрос на предоставление этого файла игнорируется.
        Примечание №2: если для указанного имени файла отсутствует версия с указанным номером,
        то запрос на предоставление этого файла игнорируется
        destination_folder - ПУть до локальной папки для сохранения объектов
        batch_size - какое количество файлов скачивание за один запрос. Рекомендуемое - 10,
        так как при бОльшем количестве могу возникать ошибки.
        """
        try:
            total_files = len(objects)
            all_downloaded_files = []  # Список успешно скачанных файлов
            failed_batches = []
            total_batches = (total_files + self.batch_size - 1) // self.batch_size

            for i in range(0, total_files, self.batch_size):
                batch = objects[i : i + self.batch_size]
                batch_num = (i // self.batch_size) + 1

                batch_result = self._download_file_batch(
                    version_id=version_id,
                    batch=batch,
                    batch_num=batch_num,
                    total_batches=total_batches,
                    destination_folder=destination_folder,
                )

                if batch_result.success:
                    all_downloaded_files.extend(batch_result.results)
                else:
                    failed_batches.append(batch_num)

            # Теперь проверяем количество УСПЕШНО СКАЧАННЫХ файлов
            successfully_downloaded_count = len(all_downloaded_files)

            if failed_batches:
                raise ModelRepoException(
                    f"❌Ошибки в батчах при скачивании файлов: {failed_batches}. | "
                    f"Скачано {successfully_downloaded_count} из {total_files} файлов в папку {destination_folder}. | "  # noqa: E501
                    f"Ожидаемые файлы: {sorted(objects)}",
                )

            if successfully_downloaded_count != total_files:
                downloaded_names = set(all_downloaded_files)
                expected_names = set(objects)
                missing_files = expected_names - downloaded_names

                raise ModelRepoException(
                    f"Скачано {successfully_downloaded_count} из {total_files} файлов в папку {destination_folder}. | "  # noqa: E501
                    f"❌Не найдены файлы: {sorted(missing_files)}. |"
                    f"Ожидаемые файлы: {sorted(expected_names)}, получено: {sorted(downloaded_names)}",
                )

            logger.info(f"✅ Все {total_files} файлов успешно скачаны в папку {destination_folder}")

            # Возвращаем полные пути ко всем скачанным файлам
            return [str(Path(destination_folder) / filename) for filename in all_downloaded_files]

        except Exception as e:
            if str(e) == "Not authorized!":
                raise ModelRepoException(
                    "❌Ошибка авторизации при скачивании файлов из ModelRepo, повторяем операцию, ожидайте..."
                ) from e
            else:
                raise ModelRepoException(
                    f"❌Неожиданная ошибка при скачивании файлов: {str(e)}"
                ) from e
    def download_model(
        self,
        version_id: str,
        objects: list[str],
        destination_folder: str,
    ) -> None:
        """
        Скачивание файла модели .zip расширения
        version_id - Идентификатор версии модели
        files - Список запрашиваемых файлов. Обязательный не пустой список.
        Допускается включать в список запрос на скачиванеи файла в двух форматах:
        1) "filename.extension" - текстовое значение, содержащее полное наименование файла,
        в таком случае предоставляется последняя версия указанного файла
        2) {"filename": "filename.extension", "version": "v2"}
        в формате словаря с указанием имени файла и номера версии.
        Примечание №1: если репозиторий не содержит файл с указанным именем,
        то запрос на предоставление этого файла игнорируется.
        Примечание №2: если для указанного имени файла отсутствует версия с указанным номером,
        то запрос на предоставление этого файла игнорируется
        destination_folder - ПУть до локальной папки для сохранения объектов

        """
        res = self.repo_client.download_files_from_repo(
            version_id=version_id,
            objects=objects,
            destination=destination_folder,
        )
        logger.info("Результат скачивания модели: %s", res)