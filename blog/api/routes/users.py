from fastapi import APIRouter,Depends,HTTPException,status,UploadFile
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from ...schemas.schemas import UserIn,UserOut,UserLogin,UserUpdate,UserOutPrivate
from ...models import models
from ...database import get_db
from datetime import datetime,timedelta,UTC,timezone
from pwdlib import PasswordHash
from sqlalchemy import select
import jwt
from ...image_utils import process_profile_image,delete_profile_pic
from ...config import settings
from PIL import UnidentifiedImageError


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


password_hash = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="users/login/",
)



def hash_password(plain_password : str)-> str:
    return password_hash.hash(plain_password)

def verify_hash(plain_password : str, hashed_password : str)-> bool:
    return password_hash.verify(plain_password,hashed_password)

def create_access_token(data:dict)-> str:
    fresh_payload = data.copy()
    fresh_payload['exp']=datetime.now(UTC)+timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    encoded_jwt = jwt.encode(fresh_payload,settings.SECRET_KEY,algorithm="HS256")
    return encoded_jwt


def decode_access_token(token : str):
    return jwt.decode(token,settings.SECRET_KEY,algorithms="HS256")

async def get_current_user(db : Annotated[AsyncSession,Depends(get_db)],token : str = Depends(oauth2_scheme) ):
    try:
        decoded_jwt = jwt.decode(token,settings.SECRET_KEY,algorithms=["HS256"])
        user_mail = decoded_jwt.get("sub")
        result = await db.execute(select(models.User).where(models.User.email == user_mail))
        user = result.scalars().first()
        return user
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=f"Sorry Authorization Error")


@router.post("/register",response_model=UserOutPrivate)
async def register_user(user_data : UserIn, db : Annotated[AsyncSession,Depends(get_db)]):
    result =await db.execute(select(models.User).where(models.User.email==user_data.email.lower()))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Email is already Used")
    user_data.password = hash_password(user_data.password)
    new_user = models.User(**user_data.model_dump())
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


@router.post("/login")
async def login_user(db : Annotated[AsyncSession , Depends(get_db)],user_data : OAuth2PasswordRequestForm = Depends(), ):
    result = await db.execute(select(models.User).where(models.User.email==user_data.username.lower()))
    existing_user = result.scalars().first()
    if not existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Invalid Credentials")
    if not verify_hash(user_data.password,existing_user.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Invalid Credentials")
    payload = {
        'sub' : existing_user.email,
    }
    token = create_access_token(payload)
    return {"access_token":token, "token_type":"Bearer"}

@router.get("/me",response_model=UserOutPrivate)
async def me(current_user : Annotated[ models.User ,Depends(get_current_user)]):
    return current_user

@router.patch("/",response_model=UserOutPrivate,status_code=status.HTTP_200_OK)
async def update_user( user_updated: UserUpdate ,db : Annotated[AsyncSession,Depends(get_db)], current_user : Annotated[ models.User ,Depends(get_current_user)]):
    user_result = await db.execute(select(models.User).where(models.User.id==current_user.id))
    user = user_result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"No User Found")
    if user_updated.password :
        user_updated.password = hash_password(user_updated.password)
    updated_user = user_updated.model_dump(exclude_unset=True)
    for key,value in updated_user.items():
        setattr(user,key,value)
    await db.commit()
    await db.refresh(user)
    return user

@router.patch("/picture",response_model=UserOutPrivate)
async def upload_profile_picture(db : Annotated[AsyncSession,Depends(get_db)],file:UploadFile,current_user : Annotated[ models.User ,Depends(get_current_user)]):
    content = await file.read()

    if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE_BYTES/ 1024 * 1024}")
    try: 
        new_filename = process_profile_image(content)
    except UnidentifiedImageError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid Image File.Please upload valid image(JPEG,PNG,GIF,Webp)") from err
    old_filename = current_user.image_file
    current_user.image_file = new_filename
    await db.commit()
    await db.refresh(current_user)

    if old_filename:
        delete_profile_pic(old_filename)
    
    return current_user

@router.delete("/picture",response_model=UserOutPrivate)
async def delete_profile(db : Annotated[AsyncSession,Depends(get_db)],current_user : Annotated[ models.User ,Depends(get_current_user)]):
    old_pic = current_user.image_file
    current_user.image_file = "default.jpg"
    delete_profile_pic(old_pic)
    await db.commit()
    await db.refresh(current_user)
    return current_user