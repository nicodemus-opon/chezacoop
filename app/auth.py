import os
import secrets
import time
from decimal import Decimal

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.db import get_db
from app.models import Role, User, Wallet
from app.services.sms import SMSService

router = APIRouter(prefix='/auth', tags=['auth'])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login')

JWT_SECRET = os.getenv('JWT_SECRET', 'change-me')
JWT_ALG = 'HS256'
TOKEN_EXPIRE_SECONDS = int(os.getenv('JWT_EXPIRE_SECONDS', '86400'))
BCRYPT_ROUNDS = int(os.getenv('BCRYPT_ROUNDS', '12'))
OTP_EXPIRE_SECONDS = 600
OTP_STORE: dict[int, tuple[str, int]] = {}


class RegisterRequest(BaseModel):
    national_id: str = Field(min_length=4, max_length=50)
    name: str = Field(min_length=2, max_length=255)
    phone: str = Field(pattern=r'^254\d{9}$')
    password: str = Field(min_length=6, max_length=255)


class LoginRequest(BaseModel):
    national_id: str = Field(min_length=4, max_length=50)
    password: str = Field(min_length=6, max_length=255)


class UserOut(BaseModel):
    id: int
    national_id: str
    name: str
    phone: str | None
    member_number: str | None
    wallet_balance: Decimal


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    user: UserOut


class VerifyOtpRequest(BaseModel):
    otp: str = Field(pattern=r'^\d{6}$')


class MessageResponse(BaseModel):
    detail: str


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')



def verify_password(password: str, stored_hash: str) -> bool:
    if not stored_hash:
        return False
    return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))



def _serialize_user(user: User) -> UserOut:
    wallet_balance = user.wallet.balance if user.wallet else Decimal('0.00')
    return UserOut(
        id=user.id,
        national_id=user.national_id,
        name=user.name,
        phone=user.phone,
        member_number=user.member_number,
        wallet_balance=wallet_balance,
    )


def _issue_token(user_id: int) -> str:
    return jwt.encode(
        {'sub': str(user_id), 'exp': int(time.time()) + TOKEN_EXPIRE_SECONDS},
        JWT_SECRET,
        algorithm=JWT_ALG,
    )


@router.post('/register', response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    existing_user = db.execute(
        select(User).where((User.national_id == payload.national_id) | (User.phone == payload.phone))
    ).scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='User already exists')

    member_role = db.execute(select(Role).where(Role.role_name == 'member')).scalar_one_or_none()
    if member_role is None:
        member_role = Role(role_name='member')
        db.add(member_role)
        db.flush()

    user = User(
        national_id=payload.national_id,
        phone=payload.phone,
        name=payload.name,
        password=hash_password(payload.password),
        role_id=member_role.id,
    )
    db.add(user)
    db.flush()

    user.member_number = f'MEM{user.id:06d}'
    wallet = Wallet(user_id=user.id, balance=Decimal('0.00'))
    db.add(wallet)

    db.commit()
    db.refresh(user)

    access_token = _issue_token(user.id)
    return AuthResponse(access_token=access_token, user=_serialize_user(user))


@router.post('/login', response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    user = db.execute(select(User).where(User.national_id == payload.national_id)).scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credentials')

    access_token = _issue_token(user.id)
    return AuthResponse(access_token=access_token, user=_serialize_user(user))


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token')

    user_id = payload.get('sub')
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token payload')

    user = db.execute(select(User).where(User.id == int(user_id))).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User not found')
    return user


@router.post('/phone/send-otp', response_model=MessageResponse)
def send_phone_otp(current_user: User = Depends(get_current_user)) -> MessageResponse:
    if not current_user.phone:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Phone number is missing')

    otp = f'{secrets.randbelow(1000000):06d}'
    OTP_STORE[current_user.id] = (otp, int(time.time()) + OTP_EXPIRE_SECONDS)

    sms = SMSService()
    sms.send_sms(current_user.phone, f'Your verification OTP is {otp}. It expires in 10 minutes.')

    return MessageResponse(detail='OTP sent successfully')


@router.post('/phone/verify', response_model=MessageResponse)
def verify_phone_otp(
    payload: VerifyOtpRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    otp_data = OTP_STORE.get(current_user.id)
    if otp_data is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='No active OTP found')

    otp_code, expires_at = otp_data
    if int(time.time()) > expires_at:
        OTP_STORE.pop(current_user.id, None)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='OTP has expired')

    if payload.otp != otp_code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid OTP')

    OTP_STORE.pop(current_user.id, None)
    current_user.phone_verified = True
    db.add(current_user)
    db.commit()

    sms = SMSService()
    member_number = current_user.member_number or 'N/A'
    sms.send_sms(current_user.phone, f'Phone verified successfully. Your member number is {member_number}.')

    return MessageResponse(detail='Phone verified successfully')


@router.get('/me', response_model=UserOut)
def me(current_user: User = Depends(get_current_user)) -> UserOut:
    return _serialize_user(current_user)
