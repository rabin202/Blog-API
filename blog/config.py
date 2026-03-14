from dotenv import load_dotenv
import os


load_dotenv()

class Config():
    DB_HOST=os.getenv('DB_HOST')
    DB_PORT=os.getenv('DB_PORT')
    DB_NAME=os.getenv('DB_NAME')
    DB_USER=os.getenv('DB_USER')
    DB_PASSWORD=os.getenv('DB_PASSWORD')
    
    
    
    SECRET_KEY="d68790f1699a7dec9416caec8ceb608bf933a175d254f4b1d24fa1155c564ac8"
    ALGORITHM="HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES=60

    MAX_UPLOAD_SIZE_BYTES = 4 * 1024 * 1024


    DB_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}" 


settings = Config()