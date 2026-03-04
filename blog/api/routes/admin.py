from fastapi import APIRouter,HTTPException,status,Depends
from ...schemas.schemas import UserOut,UserUpdate
from ...models import models
from ...database import get_db
from .users import get_current_user,hash_password
from sqlalchemy.orm import Session





router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)


def get_admin(current_user : models.User = Depends(get_current_user)):
    if current_user.role == "admin":
        return current_user
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=f"Sorry Authorization Error")


@router.get("/users",response_model=list[UserOut])
def get_users(db: Session = Depends(get_db), current_admin : models.User = Depends(get_admin)):
    print(f"{current_admin.username} accessed all users.")
    users = db.query(models.User).all()
    return users


@router.patch("/users/{user_id}",response_model=UserOut,status_code=status.HTTP_200_OK,tags=["Admin"])
def update_user(user_id : int, user_updated: UserUpdate ,db : Session = Depends(get_db), current_admin : models.User = Depends(get_current_user)):
    user = db.query(models.User).filter(models.User.id==user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"No User Found")
    if user_updated.password :
        user_updated.password = hash_password(user_updated.password)
    updated_user = user_updated.model_dump(exclude_unset=True)
    print(f"{current_admin.username} updated  users number {user_id}")
    for key,value in updated_user.items():
        setattr(user,key,value)
    db.commit()
    db.refresh(user)
    return user



@router.delete("/users/{user_id}",status_code=status.HTTP_200_OK)
def get_users(user_id : int,db: Session = Depends(get_db), current_admin : models.User = Depends(get_admin)):
    print(f"{current_admin.username} delete user with id {user_id}.")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User Not Found")
    db.delete(user)
    db.commit()
    return True