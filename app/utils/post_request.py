from logging import Logger

import httpx


async def make_request(
    url: str,
    logger: Logger,
    payload: dict | None = None,
    headers: dict | None = None,
    timeout: float = 5.0,
    verify: bool = False,
    error_class=Exception,
    json: bool = False,
    auth=None,
    get: bool = False,
) -> dict:
    try:
        async with httpx.AsyncClient(auth=auth, verify=verify, timeout=httpx.Timeout(timeout)) as client:
            if get:
                response = await client.get(url)
            else:
                logger.debug(f"Request payload: {payload}")
                if json:
                    response = await client.post(url, json=payload, headers=headers)
                else:
                    response = await client.post(url, data=payload, headers=headers)
            logger.debug(f"Raw response from api: {response.text}")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        if 500 <= e.response.status_code < 600:
            logger.exception(
                f"{error_class.__name__}: {e}; url: {e.response.url}, {e.response.text}",
            )
            raise error_class(
                f"{error_class.__name__}: {e}; url: {e.response.url}, {e.response.text}",
            ) from e
        else:
            logger.exception(f"Ошибка при выполнении запроса к url: {url}, описание: {e}")
            raise error_class(f"Ошибка при выполнении запроса к url: {url}, описание: {e}") from e
    except httpx.TimeoutException as e_timeout:
        logger.exception(f"{error_class.__name__}: ошибка таймаута {e_timeout}; url: {url}")
        raise error_class(f"{error_class.__name__}: ошибка таймаута {e_timeout}; url: {url}") from e_timeout
    except Exception as e2:
        logger.exception(f"Неожиданная ошибка: {e2} при обращении к url: {url}")
        raise Exception(f"Неожиданная ошибка: {e2} при обращении к url: {url}") from e2
