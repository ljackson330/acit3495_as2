from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from passlib.context import CryptContext
import jwt
import datetime

SECRET_KEY = "acit3495"

app = FastAPI()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory user store
users_db = {}

# Pydantic models
class User(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Helper function to hash passwords
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Helper function to verify passwords
def verify_password(plain_password, hashed_password) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Helper function to create JWT token
def create_jwt_token(username: str) -> str:
    expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    payload = {"sub": username, "exp": expiration}
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


# Register user
@app.post("/register")
def register(user: User):
    if user.username in users_db:
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_password = hash_password(user.password)
    users_db[user.username] = hashed_password
    return {"message": "User registered successfully"}


# Login user
@app.post("/login", response_model=Token)
def login(user: User):
    stored_password = users_db.get(user.username)

    if not stored_password or not verify_password(user.password, stored_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_jwt_token(user.username)
    return {"access_token": token, "token_type": "bearer"}


# Protected route example
@app.get("/protected")
def protected(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        username = payload["sub"]
        return {"message": f"Hello, {username}! This is a protected route."}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")