from fastapi import APIRouter,Depends,HTTPException,status
from ...database import get_db
from sqlalchemy.orm import selectinload
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...models import models
from ...schemas import schemas
from .users import get_current_user

router = APIRouter(
    prefix='/comments',
    tags=['Comments']
)


@router.get("/",response_model=list[schemas.CommentOut],status_code=status.HTTP_200_OK)
async def get_comments(db : Annotated[AsyncSession,Depends(get_db)], 
    current_user : Annotated[ models.User ,Depends(get_current_user)]):
    comments_result = await db.execute(select(models.Comment).where(models.Comment.user_id==current_user.id))
    comments = comments_result.scalars().all()
    return comments

@router.post("/",response_model=schemas.CommentOut,status_code=status.HTTP_200_OK)
async def create_comment(Comment_data: schemas.CommentIn, db : Annotated[AsyncSession,Depends(get_db)], 
    current_user : Annotated[ models.User ,Depends(get_current_user)]):
    check_post_result = await db.execute(select(models.Blog).where(models.Blog.id == Comment_data.blog_id))
    blog = check_post_result.scalars().first()
    if blog.is_published == False:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"No Blog Found")
    new_comment = models.Comment(**Comment_data.model_dump(),user_id=current_user.id)
    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)
    return new_comment

@router.get("/{comment_id}",response_model=schemas.CommentOut,status_code=status.HTTP_200_OK)
async def get_comment(comment_id: int ,db : Annotated[AsyncSession,Depends(get_db)], 
    current_user : Annotated[ models.User ,Depends(get_current_user)]):
    comment_result = await db.execute(select(models.Comment).options(selectinload(models.Comment.blog),selectinload(models.Comment.user)).where(models.Comment.id==comment_id))
    comment = comment_result.scalars().first()
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"No Comment Found")
    return comment


@router.patch("/{comment_id}",response_model=schemas.CommentOut,status_code=status.HTTP_200_OK)
async def update_comment(comment_id : int,blog_updated: schemas.CommentUpdate ,db : Annotated[AsyncSession,Depends(get_db)], 
    current_user : Annotated[ models.User ,Depends(get_current_user)]):
    comment_result = await db.execute(select(models.Comment).options(selectinload(models.Comment.user),selectinload(models.Comment.blog)).where(models.Comment.id==comment_id))
    comment = comment_result.scalars().first()
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"No Comment Found")
    if comment.user_id != current_user.id and current_user.role !="admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=f"Authorization Failed")
    if comment.user_id != current_user.id and current_user.role=="admin":
        print(f"{current_user.username} updated comment with id {comment.id}.")
    updated_blog = blog_updated.model_dump(exclude_unset=True)
    for key,value in updated_blog.items():
        setattr(comment,key,value)
    await db.commit()
    await db.refresh(comment)
    return comment



@router.delete("/{comment_id}",status_code=status.HTTP_200_OK)
async def delete_comment(comment_id : int,db : Annotated[AsyncSession,Depends(get_db)], 
    current_user : Annotated[ models.User ,Depends(get_current_user)]):
    commentresult = await db.execute(select(models.Comment).where(models.Comment.id==comment_id))
    comment = commentresult.scalars().first()
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"No Comment Found")
    if comment.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=f"Authorization Failed")
    if comment.user_id!=current_user.id and current_user.role == "admin":
        print(f"{current_user.username} deleted comment with id {comment_id}.")
    await db.delete(comment)
    await db.commit()
    return True