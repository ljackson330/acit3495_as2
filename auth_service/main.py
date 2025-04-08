import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from passlib.context import CryptContext
import jwt
import datetime

SECRET_KEY = os.getenv("SECRET_KEY")

app = FastAPI()

# CORS middleware to allow requests from the frontend container
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# Helper functions for password hashing and JWT token creation
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_jwt_token(username: str) -> str:
    expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    payload = {"sub": username, "exp": expiration}
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

# Load test user from environment
test_username = os.getenv("TEST_USER_NAME")
test_password = os.getenv("TEST_USER_PASSWORD")

if test_username and test_password:
    if test_username not in users_db:
        users_db[test_username] = hash_password(test_password)
        print(f"Test user '{test_username}' created at startup.")
    else:
        print(f"Test user '{test_username}' already exists.")
else:
    print("TEST_USER_NAME and/or TEST_USER_PASSWORD not set. Skipping test user creation.")

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
    print(f"Login attempt for username: {user.username}")
    stored_password = users_db.get(user.username)

    if not stored_password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(user.password, stored_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_jwt_token(user.username)
    return {"access_token": token, "token_type": "bearer"}
