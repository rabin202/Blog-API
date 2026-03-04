from fastapi import APIRouter,Depends,HTTPException,status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from ...schemas.schemas import UserIn,UserOut,UserLogin,UserUpdate
from ...models import models
from ...database import get_db
from datetime import datetime,timedelta,UTC,timezone
from pwdlib import PasswordHash
import jwt
from ...config import settings



router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


password_hash = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/login/",
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


@router.post("/register",response_model=UserOut)
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
def login_user(user_data : UserLogin, db : Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email==user_data.email.lower()).first()
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

@router.get("/me",response_model=UserOut)
def me(current_user : models.User = Depends(get_current_user)):
    return current_user

@router.patch("/",response_model=UserOut,status_code=status.HTTP_200_OK)
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