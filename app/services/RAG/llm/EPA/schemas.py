from pydantic import BaseModel


class EPAToken(BaseModel):
    access_token: str
    expires_in: int
    token_type: str
