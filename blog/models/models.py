from __future__ import annotations
from ..database import Base
from sqlalchemy.orm import relationship,Mapped,mapped_column
from sqlalchemy import String,Boolean,Integer,Text,ForeignKey,func,CheckConstraint
from datetime import datetime
from pydantic import ConfigDict
from typing import List


class User(Base):
    __tablename__="users"
    
    id : Mapped[int] = mapped_column(primary_key=True,nullable=False,index=True,unique=True)
    username : Mapped[str] = mapped_column(String(30),nullable=False,unique=True,index=True)
    email : Mapped[str] = mapped_column(String(100),nullable=False,unique=True)
    created_at : Mapped[datetime] = mapped_column(server_default=func.now())
    password : Mapped[str] = mapped_column(String(100),nullable=False)
    role : Mapped[str] = mapped_column(String,CheckConstraint("role IN ('admin','guest')"),server_default="guest")
    image_file : Mapped[str] = mapped_column(String(200),nullable=True,default=None)

    blogs : Mapped[List['Blog']] = relationship(back_populates="author",cascade="all,delete-orphan")
    comments : Mapped[List['Comment']] = relationship(back_populates="user",cascade="all,delete-orphan")

    @property
    def profile_image_path(self):
        if self.image_file:
            return f"media/profile_pics/{self.image_file}"
        return f"static/profile_pics/default.jpg"
    

    
class Blog(Base):
    __tablename__="blogs"

    id : Mapped[int] =mapped_column(index=True,primary_key=True,nullable=False,unique=True)
    title : Mapped[str]= mapped_column(String(100))
    content : Mapped[str]=mapped_column(Text,nullable=False)
    created_at : Mapped[datetime]= mapped_column(server_default=func.now())
    updated_at : Mapped[datetime]= mapped_column(server_default=func.now(),onupdate=func.now())
    author_id : Mapped[int] = mapped_column(ForeignKey("users.id",ondelete="CASCADE"),nullable=False)
    is_published : Mapped[int] = mapped_column(Boolean,nullable=False,index=True)

    

    author : Mapped['User'] = relationship(back_populates="blogs")
    comments : Mapped[List['Comment']] = relationship(back_populates="blog")




class Comment(Base):
    __tablename__="comments"

    id : Mapped[int] = mapped_column(index=True,primary_key=True,nullable=False,unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id",ondelete="CASCADE"),nullable=False)
    blog_id: Mapped[int] = mapped_column(ForeignKey("blogs.id",ondelete="CASCADE"),nullable=False)
    user : Mapped['User'] = relationship(back_populates="comments")
    blog : Mapped['Blog'] = relationship(back_populates="comments")
    body : Mapped[str] = mapped_column(String(200),nullable=False)
    created_at : Mapped[datetime]=mapped_column(server_default=func.now())
    updated_at : Mapped[datetime]=mapped_column(server_default=func.now(),onupdate=func.now())

