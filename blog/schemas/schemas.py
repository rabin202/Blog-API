from __future__ import annotations
from enum import Enum

from pydantic import BaseModel,Field,EmailStr
from datetime import datetime
from typing import Optional,List


class UserRole(str, Enum):
    ADMIN = "admin"
    GUEST = "guest"


class User(BaseModel):
    email : EmailStr
    username : str = Field(max_length=40,min_length=1)

class UserIn(User):
    password : str = Field(min_length=8)


class UserLogin(BaseModel):
    email : EmailStr
    password : str 


class UserOut(User):
    id : int 
    created_at : datetime
    role : UserRole

class UserUpdate(BaseModel):
    email : Optional[EmailStr] = None
    username : Optional[str] = None
    password : Optional[str] = None


class BlogBase(BaseModel):
    title : str = Field(max_length=100,min_length=1)
    content : str = Field(max_length=200)
    is_published : Optional[bool] = True

class BlogIn(BlogBase):
    pass

class BlogUpdate(BaseModel):
    title : Optional[str]   = None
    content : Optional[str] = None
    is_published : Optional[bool] = None

class BlogOut(BlogBase):
    id : int
    created_at : datetime
    updated_at : datetime
    is_published : bool
    author : UserOut
    comments : List[CommentOut]

    class Config:
        from_attributes=True


class Token(BaseModel):
    access_token : str
    token_type : str


class Comment(BaseModel):
    body : str = Field(max_length=200,min_length=1)
    blog_id : int

class CommentIn(Comment):
    pass

class CommentOut(Comment):
    id : int 
    user : UserOut
    created_at : datetime
    updated_at : datetime

class CommentUpdate(BaseModel):
    body : Optional[str] = None

