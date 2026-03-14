from fastapi import APIRouter,Depends,HTTPException,status,Query
from ...database import get_db
from sqlalchemy import func,select
from sqlalchemy.orm import selectinload,joinedload
from ...models import models
from ...schemas import schemas
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from .users import get_current_user

router = APIRouter(
    prefix='/blogs',
    tags=['Blogs']
)


@router.get("/myblogs",response_model=schemas.PaginationBlogResponse,status_code=status.HTTP_200_OK)
async def get_my_blogs(
    db : Annotated[AsyncSession,Depends(get_db)], 
    current_user : Annotated[ models.User ,Depends(get_current_user)], 
    limit : int = Query(5,ge=1,le=10), offset : int =Query(0,ge=0),order : str = Query("DESC")
    ):
    base_query = select(models.Blog).options(selectinload(models.Blog.comments)).where(models.Blog.author_id==current_user.id)
    if order == "ASC":
        base_query = base_query.order_by(models.Blog.created_at.asc())
    else:
        base_query = base_query.order_by(models.Blog.created_at.desc())
    
    count_query = select(func.count()).where(models.Blog.author_id==current_user.id)

    count_result = await db.execute(count_query)
    total = count_result.scalar_one() or 0
    base_result = await db.execute(base_query.offset(offset).limit(limit))
    blogs = base_result.scalars().all()
    has_more = total > offset + limit
    return schemas.PaginationBlogResponse(
        blogs=[schemas.BlogOut.model_validate(blog) for  blog in blogs]
        ,limit=limit,offset=offset,total=total,has_more=has_more,)



@router.get("/",response_model=schemas.PaginationBlogResponse,status_code=status.HTTP_200_OK)
async def get_blogs(db : Annotated[AsyncSession,Depends(get_db)], 
    current_user : Annotated[ models.User ,Depends(get_current_user)],s : str = Query(None,min_length=1), limit : int = Query(5,ge=1,le=10), offset : int =Query(0,ge=0),order : str = Query("DESC")):    
    if s:
        base_query = select(models.Blog).options(selectinload(models.Blog.comments),selectinload(models.Blog.author)).where(models.Blog.is_published==True,models.Blog.title.contains(s))
    else:
        base_query = select(models.Blog).options(selectinload(models.Blog.comments),selectinload(models.Blog.author)).where(models.Blog.is_published==True )
    if order == "ASC":
        base_query = base_query.order_by(models.Blog.created_at.asc())
    else:
        base_query = base_query.order_by(models.Blog.created_at.desc())
    count_query = select(func.count()).where(models.Blog.is_published==True)
    count_result =await db.execute(count_query)
    total = count_result.scalar_one() or 0
    base_result = await db.execute(base_query.offset(offset).limit(limit))
    blogs =base_result.scalars().all()
    has_more = total > offset + limit 
    return schemas.PaginationBlogResponse(
        blogs=[schemas.BlogOut.model_validate(blog) for  blog in blogs]
        ,limit=limit,offset=offset,total=total,has_more=has_more)


@router.get("/{user_id}/blogs",response_model=list[schemas.BlogOut],status_code=status.HTTP_200_OK,tags=["Admin"])
async def get_user_blogs(user_id : int,db : Annotated[AsyncSession,Depends(get_db)], 
    current_user : Annotated[ models.User ,Depends(get_current_user)], limit : int = Query(5,ge=1,le=10), offset : int =Query(0,ge=0),order : str = Query("DESC")):
    user_check_result = await db.execute(select(models.User).where(models.User.id==user_id))
    page_user = user_check_result.scalars().first()
    if not page_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User Not found")
    
    if (current_user.id != user_id and current_user.role != "admin"):
        base_query = select(models.Blog).options(selectinload(models.Blog.author)).where(models.Blog.author_id==user_id, models.Blog.is_published==True)
    else:
        base_query = select(models.Blog).options(selectinload(models.Blog.author)).where(models.Blog.author_id==user_id)
    
    if order == "ASC":
        base_query = base_query.order_by(models.Blog.created_at.asc())
    else:
        base_query = base_query.order_by(models.Blog.created_at.desc())

    base_result =await db.execute(base_query.options(selectinload(models.Blog.comments)).limit(limit).offset(offset))
    blogs = base_result.scalars().all()
    return blogs



@router.post("/",response_model=schemas.BlogOut,status_code=status.HTTP_200_OK)
async def create_blog(Blog_Data: schemas.BlogIn ,db : Annotated[AsyncSession,Depends(get_db)], 
    current_user : Annotated[ models.User ,Depends(get_current_user)]):
    new_blog = models.Blog(**Blog_Data.model_dump(),author_id=current_user.id)
    db.add(new_blog)
    await db.commit()
    await db.refresh(new_blog)
    result =await  db.execute(
        select(models.Blog).options(selectinload(models.Blog.comments)).where(models.Blog.id == new_blog.id)
    )
    added_blog = result.scalar_one()
    return added_blog

@router.get("/{blog_id}",response_model=schemas.BlogOut,status_code=status.HTTP_200_OK,tags=["Admin"])
async def get_blog(blog_id: int ,db : Annotated[AsyncSession,Depends(get_db)], 
    current_user : Annotated[ models.User ,Depends(get_current_user)]):
    base_query = select(models.Blog).options(selectinload(models.Blog.comments),selectinload(models.Blog.author)).where(models.Blog.id==blog_id)
    blog_result =await db.execute(base_query)
    blog = blog_result.scalars().first()
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"No Blog Found")
    if not blog.is_published:
        if blog.author_id != current_user.id and current_user.role!="admin":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail=f"Authorization Failed")
        if current_user.role=="admin" and blog.author_id!=current_user.id:
            print(f"{current_user.username} fetched blog number {blog.id}")
    return blog


@router.patch("/{blog_id}",response_model=schemas.BlogOut,status_code=status.HTTP_200_OK,tags=["Admin"])
async def update_blog(blog_id : int,blog_updated: schemas.BlogUpdate ,db : Annotated[AsyncSession,Depends(get_db)], 
    current_user : Annotated[ models.User ,Depends(get_current_user)]):
    blog_result= await db.execute(select(models.Blog).options(selectinload(models.Blog.comments)).where(models.Blog.id==blog_id))
    blog = blog_result.scalars().first()
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
    await db.commit()
    await db.refresh(blog)
    return blog



@router.delete("/{blog_id}",status_code=status.HTTP_200_OK,tags=["Admin"])
async def delete_blog(blog_id : int,db : Annotated[AsyncSession,Depends(get_db)], 
    current_user : Annotated[ models.User ,Depends(get_current_user)]):
    blog_result = await db.execute(select(models.Blog).where(models.Blog.id==blog_id))
    blog = blog_result.scalars().first()
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"No Blog Found")
    if blog.author_id != current_user.id and current_user.role!="admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=f"Authorization Failed")
    if current_user.role=="admin" and blog.author_id!=current_user.id:
        print(f"{current_user.username} updated blog number {blog.id}")
        print(blog)
    
    await db.delete(blog)
    await db.commit()
    return True
    