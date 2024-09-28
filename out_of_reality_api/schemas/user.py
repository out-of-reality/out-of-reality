from pydantic import BaseModel


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    access_token: str


class UserData(BaseModel):
    name: str


class UserFaceIDLogin(BaseModel):
    image: str
