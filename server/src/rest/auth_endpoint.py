from fastapi import APIRouter, Depends, HTTPException, status, Header
from typing import Optional

from rest.models.login_data import LoginData
from rest.models.user_response_data import UserResponseData
from rest.models.login_response import LoginResponse
from rest.models.user_data import UserData
from rest.models.token_data import TokenData

from service.auth_service import AuthService
from utils.logger import get_logger


log = get_logger("AuthEndpoint")
router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post(
    "/register",
    responses={
        200: {"model": UserResponseData, "description": "Successful response"},
    },
    response_model_by_alias=True,
)
async def register(user_data: UserData, auth_service: AuthService = Depends()):
    """Регистрация пользователя"""
    log.info(f"Register request email: {user_data.email}",  extra={"email": user_data.email})
    await auth_service.register_user(user_data)
    log.info(f"Send link on email: {user_data.email}", exc_info={"email": user_data.email})



@router.post(
    "/login",
    responses={
        200: {"model": TokenData, "description": "Successful response"},
    },
    response_model_by_alias=True,
)
async def login(login_data: LoginData, auth_service: AuthService = Depends()) -> LoginResponse | str:
    """Авторизация пользователя"""
    log.info(f"Login attempt for email: {login_data.email}")
    response = await auth_service.authenticate_user(login_data)
    return response


@router.get(
    "/me",
    responses={
        200: {"model": UserResponseData, "description": "Successful response"},
    },
    response_model_by_alias=True,
)
async def get_current_user(
    authorization: Optional[str] = Header(None),
    auth_service: AuthService = Depends()
) -> UserResponseData:
    """Получение информации о пользователе"""
    if not authorization or not authorization.startswith("Bearer "):
        log.warning("Invalid or missing authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = authorization.replace("Bearer ", "")
    user = await auth_service.get_user_by_token(token)
    
    if not user:
        log.warning("Invalid token or user not found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    log.info(f"Get current user request for {user.email}")
    return UserResponseData(email=user.email, name=user.name)
