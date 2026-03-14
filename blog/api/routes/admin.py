from fastapi import APIRouter,HTTPException,status,Depends,Query
from ...schemas.schemas import UserOut,UserUpdate,PaginationUserResponse
from ...models import models
from ...database import get_db
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select,func
from .users import get_current_user,hash_password
from ...image_utils import delete_profile_pic
from sqlalchemy.orm import Session





router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)


async def get_admin(current_user : models.User = Depends(get_current_user)):
    if current_user.role == "admin":
        return current_user
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=f"Sorry Authorization Error")


@router.get("/users",response_model=PaginationUserResponse)
async def get_users(db:  Annotated[AsyncSession,Depends(get_db)], current_admin : Annotated[models.User,Depends(get_admin)], limit : int = Query(5,ge=1,le=10), offset : int =Query(0,ge=0)):
    print(f"{current_admin.username} accessed all users.")
    users_result = await db.execute((select(models.User)).offset(offset).limit(limit))
    count_query = await db.execute(select(func.count()).select_from(models.User))
    users = users_result.scalars().all()
    total = count_query.scalar_one() or 0
    hasmore = total > (offset + limit)
    return PaginationUserResponse(
        users=[UserOut.model_validate(user) for  user in users]
        ,limit=limit,offset=offset,total=total,has_more=hasmore)


@router.patch("/users/{user_id}",response_model=UserOut,status_code=status.HTTP_200_OK,tags=["Admin"])
async def update_user(user_id : int, user_updated: UserUpdate ,db:  Annotated[AsyncSession,Depends(get_db)], current_admin : Annotated[models.User,Depends(get_admin)]):
    user_result = await db.execute(select(models.User).where(models.User.id==user_id))
    print(user_result)
    user = user_result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"No User Found")
    if user_updated.password :
        user_updated.password = hash_password(user_updated.password)
    updated_user = user_updated.model_dump(exclude_unset=True)
    print(f"{current_admin.username} updated  users number {user_id}")
    for key,value in updated_user.items():
        setattr(user,key,value)
    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/users/{user_id}",status_code=status.HTTP_200_OK)
async def delete_user(user_id : int,db: Session = Depends(get_db), current_admin : models.User = Depends(get_admin)):
    print(f"{current_admin.username} delete user with id {user_id}.")
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User Not Found")
    old_filename = user.image_file
    await db.delete(user)
    delete_profile_pic(old_filename)
    await db.commit()
    return True