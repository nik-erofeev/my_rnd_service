from pydantic import BaseModel, Field


class Tokens(BaseModel):
    access_token: str = Field(..., description="токен доступа")
    refresh_token: str = Field(..., description="токен обновления")
    id_token: str = Field(..., description="ID токен")
    expires_in: int = Field(..., description="время жизни access_token")
    refresh_expires_in: int = Field(..., description="время жизни refresh_token")
    token_type: str = Field(..., description="тип токена")
    session_state: str = Field(..., description="состояние сессии")
    scope: str = Field(..., description="область действия токена")
