from fastapi import APIRouter,Depends,HTTPException,status,Query
from ...database import get_db
from sqlalchemy.orm import Session
from ...models import models
from ...schemas import schemas
from .users import get_current_user

router = APIRouter(
    prefix='/blogs',
    tags=['Blogs']
)


@router.get("/myblogs",response_model=list[schemas.BlogOut],status_code=status.HTTP_200_OK)
def get_my_blogs(db : Session = Depends(get_db), current_user : models.User = Depends(get_current_user), limit : int = Query(5,ge=1,le=10), offset : int =Query(0,ge=0),order : str = Query("DESC")):
    if order == "ASC":
        query = db.query(models.Blog).filter(models.Blog.author_id==current_user.id).order_by(models.Blog.created_at.asc())
    else:
        query = db.query(models.Blog).filter(models.Blog.author_id==current_user.id).order_by(models.Blog.created_at.desc())
        
    blogs = query.offset(offset).limit(limit).all()
    return blogs



@router.get("/",response_model=list[schemas.BlogOut],status_code=status.HTTP_200_OK)
def get_blogs(db : Session = Depends(get_db), current_user : models.User = Depends(get_current_user),s : str = Query(None,min_length=1), limit : int = Query(5,ge=1,le=10), offset : int =Query(0,ge=0),order : str = Query("DESC")):
    print(s)
    if s:
        query = db.query(models.Blog).filter(models.Blog.is_published==True,models.Blog.title.contains(s))
    else:
        query = db.query(models.Blog).filter(models.Blog.is_published==True )
    if order == "ASC":
        db_query = query.order_by(models.Blog.created_at.asc())
    else:
        db_query = query.order_by(models.Blog.created_at.desc())
    blogs = db_query.offset(offset).limit(limit).all()
    return blogs


@router.get("/{user_id}",response_model=list[schemas.BlogOut],status_code=status.HTTP_200_OK,tags=["Admin"])
def get_user_blogs(user_id : int,db : Session = Depends(get_db), current_user : models.User = Depends(get_current_user), limit : int = Query(5,ge=1,le=10), offset : int =Query(0,ge=0),order : str = Query("DESC")):
    if order == "ASC":
        db_query = db.query(models.Blog).order_by(models.Blog.created_at.asc())
    else:
        db_query = db.query(models.Blog).order_by(models.Blog.created_at.desc())

    
    if current_user.id != user_id and current_user.role != "admin":
        blogs = db_query.filter(models.Blog.author_id==user_id and models.Blog.is_published==True).offset(offset).limit(limit).all()
    else:
        blogs = db_query.filter(models.Blog.author_id==user_id).offset(offset).limit(limit).all()
    return blogs



@router.post("/",response_model=schemas.BlogOut,status_code=status.HTTP_200_OK)
def create_blog(Blog_Data: schemas.BlogIn ,db : Session = Depends(get_db), current_user : models.User = Depends(get_current_user)):
    new_blog = models.Blog(**Blog_Data.model_dump(),author_id=current_user.id)
    db.add(new_blog)
    db.commit()
    db.refresh(new_blog)
    return new_blog

@router.get("/{blog_id}",response_model=schemas.BlogOut,status_code=status.HTTP_200_OK,tags=["Admin"])
def get_blog(blog_id: int ,db : Session = Depends(get_db), current_user : models.User = Depends(get_current_user)):
    blog = db.query(models.Blog).filter(models.Blog.id==blog_id).first()
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"No Blog Found")
    if blog.author_id != current_user.id and current_user.role!="admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=f"Authorization Failed")
    if current_user.role=="admin" and blog.author_id!=current_user.id:
        print(f"{current_user.username} fetched blog number {blog.id}")
    return blog


@router.patch("/{blog_id}",response_model=schemas.BlogOut,status_code=status.HTTP_200_OK,tags=["Admin"])
def update_blog(blog_id : int,blog_updated: schemas.BlogUpdate ,db : Session = Depends(get_db), current_user : models.User = Depends(get_current_user)):
    blog = db.query(models.Blog).filter(models.Blog.id==blog_id).first()
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"No Blog Found")
    if blog.author_id != current_user.id and current_user.role!="admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=f"Authorization Failed")
    if current_user.role=="admin" and blog.author_id!=current_user.id:
        print(f"{current_user.username} updated blog number {blog.id}")
    updated_blog = blog_updated.model_dump(exclude_unset=True)
    for key,value in updated_blog.items():
        setattr(blog,key,value)
    db.commit()
    db.refresh(blog)
    return blog



@router.delete("/{blog_id}",status_code=status.HTTP_200_OK,tags=["Admin"])
def delete_blog(blog_id : int,db : Session = Depends(get_db), current_user : models.User = Depends(get_current_user)):
    blog = db.query(models.Blog).filter(models.Blog.id==blog_id).first()
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"No Blog Found")
    if blog.author_id != current_user.id and current_user.role!="admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=f"Authorization Failed")
    if current_user.role=="admin" and blog.author_id!=current_user.id:
        print(f"{current_user.username} updated blog number {blog.id}")
        print(blog)
    
    db.delete(blog)
    db.commit()
    return True
    