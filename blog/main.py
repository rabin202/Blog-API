from fastapi import FastAPI
from .api.routes import blogs,users,comments,admin




app = FastAPI()

app.include_router(blogs.router)
app.include_router(users.router)
app.include_router(comments.router)
app.include_router(admin.router)

@app.get("/")
def main():
    return {"Health":"Positive"}