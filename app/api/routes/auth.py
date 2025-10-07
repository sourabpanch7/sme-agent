from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from ..deps import get_db
from ..utils.auth import create_jwt, verify_jwt

router = APIRouter()

class LoginIn(BaseModel):
    user_id: str

@router.post('/login')
def login(payload: LoginIn):
    token = create_jwt({'sub': payload.user_id})
    return {'access_token': token}

@router.get('/verify')
def verify(token: str):
    payload = verify_jwt(token)
    return payload