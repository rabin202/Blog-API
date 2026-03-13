from fastapi import APIRouter,Depends,HTTPException,status,UploadFile
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ...schemas.schemas import UserIn,UserOut,UserLogin,UserUpdate,UserOutPrivate
from ...models import models
from ...database import get_db
from datetime import datetime,timedelta,UTC,timezone
from pwdlib import PasswordHash
import jwt
from ...image_utils import process_profile_image,delete_profile_pic
from ...config import settings
from PIL import UnidentifiedImageError
import asyncio


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

def get_current_user(token : str = Depends(oauth2_scheme), db : Session = Depends(get_db)):
    try:
        decoded_jwt = jwt.decode(token,settings.SECRET_KEY,algorithms=["HS256"])
        user_mail = decoded_jwt.get("sub")
        user = db.query(models.User).filter(models.User.email == user_mail).first()
        return user
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=f"Sorry Authorization Error")


@router.post("/register",response_model=UserOutPrivate)
def register_user(user_data : UserIn, db : Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email==user_data.email.lower()).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Email is already Used")
    user_data.password = hash_password(user_data.password)
    new_user = models.User(**user_data.model_dump())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login")
def login_user(user_data : OAuth2PasswordRequestForm = Depends(), db : Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email==user_data.username.lower()).first()
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
def me(current_user : models.User = Depends(get_current_user)):
    return current_user

@router.patch("/",response_model=UserOutPrivate,status_code=status.HTTP_200_OK)
def update_user( user_updated: UserUpdate ,db : Session = Depends(get_db), current_user : models.User = Depends(get_current_user)):
    user = db.query(models.User).filter(models.User.id==current_user.id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"No User Found")
    if user_updated.password :
        user_updated.password = hash_password(user_updated.password)
    updated_user = user_updated.model_dump(exclude_unset=True)
    for key,value in updated_user.items():
        setattr(user,key,value)
    db.commit()
    db.refresh(user)
    return user

@router.patch("/picture",response_model=UserOutPrivate)
async def upload_profile_picture(file:UploadFile,current_user : models.User = Depends(get_current_user),db : Session = Depends(get_db)):
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
    db.commit()
    db.refresh(current_user)

    if old_filename:
        delete_profile_pic(old_filename)
    
    return current_user

@router.delete("/picture",response_model=UserOutPrivate)
def delete_profile(current_user : models.User = Depends(get_current_user),db:Session = Depends(get_db)):
    old_pic = current_user.image_file
    current_user.image_file = "default.jpg"
    delete_profile_pic(old_pic)
    db.commit()
    db.refresh(current_user)
    return current_user