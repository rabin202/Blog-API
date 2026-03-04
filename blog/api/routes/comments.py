from fastapi import APIRouter,Depends,HTTPException,status
from ...database import get_db
from sqlalchemy.orm import Session
from ...models import models
from ...schemas import schemas
from .users import get_current_user

router = APIRouter(
    prefix='/comments',
    tags=['Comments']
)


@router.get("/",response_model=list[schemas.CommentOut],status_code=status.HTTP_200_OK)
def get_comments(db : Session = Depends(get_db), current_user : models.User = Depends(get_current_user)):
    comments = db.query(models.Comment).filter(models.Comment.user_id==current_user.id).all()
    return comments

@router.post("/",response_model=schemas.CommentOut,status_code=status.HTTP_200_OK)
def create_comment(Comment_data: schemas.CommentIn, db : Session = Depends(get_db), current_user : models.User = Depends(get_current_user)):
    new_comment = models.Comment(**Comment_data.model_dump(),user_id=current_user.id)
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment

@router.get("/{comment_id}",response_model=schemas.CommentOut,status_code=status.HTTP_200_OK)
def get_comment(comment_id: int ,db : Session = Depends(get_db), current_user : models.User = Depends(get_current_user)):
    comment = db.query(models.Comment).filter(models.Comment.id==comment_id).first()
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"No Comment Found")
    return comment


@router.patch("/{comment_id}",response_model=schemas.CommentOut,status_code=status.HTTP_200_OK)
def update_comment(comment_id : int,blog_updated: schemas.CommentUpdate ,db : Session = Depends(get_db), current_user : models.User = Depends(get_current_user)):
    comment = db.query(models.Comment).filter(models.Comment.id==comment_id).first()
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
    db.commit()
    db.refresh(comment)
    return comment



@router.delete("/{comment_id}",status_code=status.HTTP_200_OK)
def delete_comment(comment_id : int,db : Session = Depends(get_db), current_user : models.User = Depends(get_current_user)):
    comment = db.query(models.Comment).filter(models.Comment.id==comment_id).first()
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"No Comment Found")
    if comment.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=f"Authorization Failed")
    if comment.user_id!=current_user.id and current_user.role == "admin":
        print(f"{current_user.username} deleted comment with id {comment_id}.")
    db.delete(comment)
    db.commit()
    return True