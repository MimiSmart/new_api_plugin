from datetime import datetime, timedelta
from typing import Annotated, Union

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

import tools

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 3 * 24 * 60


class Auth():
    keys = []

    filename = "new_api_plugin.sqlite3"
    users: list
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

    class Token(BaseModel):
        access_token: str
        token_type: str

    class TokenData(BaseModel):
        username: Union[str, None] = None

    class User(BaseModel):
        username: str = None
        hashed_password: str = None

    def authenticate_user(self, key: str):
        keys = tools.read_keys()
        if key in keys:
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = self.create_access_token(
                data={"sub": key}, expires_delta=access_token_expires
            )
            return {"access_token": access_token, "token_type": "bearer"}
        return False

    def create_access_token(self, data: dict, expires_delta: Union[timedelta, None] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    async def get_current_user(self, token: Annotated[str, Depends(oauth2_scheme)]):
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user: str = payload.get("sub")
            keys = tools.read_keys()
            if user is None or user not in keys:
                return False
        except JWTError:
            return False
        return user
