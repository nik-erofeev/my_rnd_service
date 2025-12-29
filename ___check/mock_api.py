from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()


@app.post("/test/pim.logger.efk")
async def handle_anything_elk(request: Request):
    """
    Принимает любой тип данных в теле запроса и возвращает 200 OK.
    """
    try:
        body = await request.json()
        print(body)

        # message = body.get("event").get("message").get("message")
        # if message:
        #     print(f"message_ELK: {message}")

    except Exception:
        # Если не JSON — просто вернём сырые данные
        body = await request.body()

    return JSONResponse(
        content={
            "message": "OK",
            # "received": str(body),
        },
        status_code=200,
    )


@app.post("/test/pim.logger.db")
async def handle_anything_db(request: Request):
    """
    Принимает любой тип данных в теле запроса и возвращает 200 OK.
    """
    try:
        body = await request.json()

        print(body)
        # message = body.get("message")
        # if message:
        #     print(f"message_DB: {message}")

    except Exception:
        # Если не JSON — просто вернём сырые данные
        body = await request.body()

    return JSONResponse(
        content={
            "message": "OK",
            # "received": str(body),
        },
        status_code=200,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("___check.mock_api:app", host="0.0.0.0", port=8010, reload=True)
