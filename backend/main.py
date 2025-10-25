from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import bcrypt
import re
import uuid
import jwt as pyjwt
from datetime import datetime, timedelta
from typing import List
import os
import logging


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


DATABASE_URL = "sqlite:///smartbank.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Base = declarative_base()

# SQLAlchemy Models
class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True)
    mobile_number = Column(String)
    documents = Column(String)
    password = Column(String) 
    kyc_status = Column(String, default="pending")

class AccountDB(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    account_number = Column(String, unique=True)
    balance = Column(Float)
    acc_type = Column(String)

class TransactionDB(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    from_account = Column(String)
    to_account = Column(String)
    amount = Column(Float)
    timestamp = Column(String)

Base.metadata.create_all(bind=engine)

# Database Session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# JWT Config
SECRET_KEY = "" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI()


origins = [
    "http://127.0.0.1:5173",
    "http://localhost:5173/register",
    "http://localhost:5173/login",
    "http://localhost:5173/create-account",
    "http://localhost:5173/dashboard/:userId",

]
    

app.add_middleware(
    CORSMiddleware, # type: ignore
    allow_origins=origins,      
    allow_credentials=True,
    allow_methods=["*"],        
    allow_headers=["*"],        
)
# Pydantic Models
class User(BaseModel):
    name: str
    email: str
    password: str
    mobile_number: str | None = None

class Account(BaseModel):
    user_id: str
    acc_type: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Helper Functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return pyjwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(OAuth2PasswordBearer(tokenUrl="login")), db: Session = Depends(get_db)):
    try:
        payload = pyjwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return user_id
    except pyjwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

# Endpoints
@app.get("/")
async def root():
    return {"msg": "API is working"}
@app.post("/verify-kyc/{user_id}")
async def verify_kyc(user_id: int, approve: bool, db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.kyc_status = "approved" if approve else "rejected"
    db.commit()
    return {"message": f"KYC {user.kyc_status}"}
@app.post("/register")
async def register(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    mobile_number: str = Form(None),
    documents: List[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    try:
     
        if db.query(UserDB).filter(UserDB.email == email).first():
            raise HTTPException(status_code=400, detail="Email already registered")

        
        PASSWORD_REGEX = re.compile(
            r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{8,}$"
        )
        if not PASSWORD_REGEX.match(password):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Password must contain at least 8 characters, "
                    "including one uppercase letter, one lowercase letter, "
                    "one number, and one special character."
                ),
            )

  
        hashed_pw = hash_password(password)

     
        ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png'}
        os.makedirs("uploads", exist_ok=True)
        doc_paths = []

        if documents:
            for doc in documents:
                ext = os.path.splitext(doc.filename)[1].lower()
                if ext not in ALLOWED_EXTENSIONS:
                    raise HTTPException(
                        status_code=400,
                        detail=f"File {doc.filename} not allowed. Only JPG, JPEG, PNG allowed."
                    )

                
                unique_filename = f"{uuid.uuid4().hex}_{doc.filename}"
                file_path = os.path.join("uploads", unique_filename)

               
                content = await doc.read()
                if len(content) > 5 * 1024 * 1024:
                    raise HTTPException(
                        status_code=400,
                        detail=f"File {doc.filename} exceeds 5MB limit"
                    )

                with open(file_path, "wb") as f:
                    f.write(content)

                doc_paths.append(file_path)


        user = UserDB(
            name=name,
            email=email,
            password=hashed_pw,
            mobile_number=mobile_number,
            documents=",".join(doc_paths) if doc_paths else None,
            kyc_status="pending",
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return {"message": "User registered", "user_id": str(user.id)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in register endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/account")
async def create_account(account: Account, current_user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user != account.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    import random
    account_number = f"ACCT-{int(datetime.now().timestamp())}-{random.randint(1000, 9999)}"
    
    account_data = AccountDB(
        user_id=int(account.user_id),
        account_number=account_number,
        balance=500,
        acc_type=account.acc_type
    )
    db.add(account_data)
    db.commit()
    
    transaction = TransactionDB(
        from_account="INITIAL_DEPOSIT",
        to_account=account_number,
        amount=500,
        timestamp=datetime.now().isoformat()
    )
    db.add(transaction)
    db.commit()
    
    return {"message": "Account created", "account_id": str(account_data.id)}

@app.get("/dashboard/{user_id}")
async def get_dashboard(user_id: str, current_user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    accounts = db.query(AccountDB).filter(AccountDB.user_id == int(user_id)).all()
    account_numbers = [acc.account_number for acc in accounts]
    transactions = db.query(TransactionDB).filter(
        TransactionDB.from_account.in_(account_numbers) | TransactionDB.to_account.in_(account_numbers)
    ).all()
    
    accounts_dict = [{"user_id": str(acc.user_id), "account_number": acc.account_number, "balance": acc.balance, "acc_type": acc.acc_type} for acc in accounts]
    transactions_dict = [{"from_account": tx.from_account, "to_account": tx.to_account, "amount": tx.amount, "timestamp": tx.timestamp} for tx in transactions]
    
    return {"accounts": accounts_dict, "transactions": transactions_dict}

# from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
# from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
# from pydantic import BaseModel
# from pymongo import MongoClient
# from bson import ObjectId
# import bcrypt
# import jwt
# from datetime import datetime, timedelta
# from typing import List


# MONGO_URI = "mongodb+srv://smarees477529_db_user:<IC2QVr6fNZKeMmQW>@banking.bjvulzt.mongodb.net/?appName=Banking"
# client = MongoClient(MONGO_URI)
# db = client.smartbank  # Database name
# users_collection = db.users
# accounts_collection = db.accounts
# transactions_collection = db.transactions

# # JWT Config
# SECRET_KEY = "your_secret_key"  # Change this to a strong secret
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 30

# app = FastAPI()

# # Models
# class User(BaseModel):
#     name: str
#     email: str
#     password: str

# class Account(BaseModel):
#     user_id: str
#     acc_type: str 

# class Token(BaseModel):
#     access_token: str
#     token_type: str

# # Helper Functions
# def hash_password(password: str) -> str:
#     return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

# def create_access_token(data: dict, expires_delta: timedelta = None):
#     to_encode = data.copy()
#     expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
#     to_encode.update({"exp": expire})
#     return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# async def get_current_user(token: str = Depends(OAuth2PasswordBearer(tokenUrl="login"))):
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         user_id: str = payload.get("sub")
#         if user_id is None:
#             raise HTTPException(status_code=401, detail="Invalid authentication credentials")
#         return user_id
#     except jwt.PyJWTError:
#         raise HTTPException(status_code=401, detail="Invalid authentication credentials")

# # Endpoints

# @app.post("/register")
# async def register(
#     name: str = Form(...),
#     email: str = Form(...),
#     password: str = Form(...),
#     documents: List[UploadFile] = File(None)  # Optional documents
# ):
#     if users_collection.find_one({"email": email}):
#         raise HTTPException(status_code=400, detail="Email already registered")
    
#     hashed_pw = hash_password(password)
#     user_data = {"name": name, "email": email, "password": hashed_pw, "documents": []}
    
#     if documents:
#         for doc in documents:
#             content = await doc.read()
#             user_data["documents"].append({"filename": doc.filename, "content": content})  # Store as binary
    
#     result = users_collection.insert_one(user_data)
#     return {"message": "User registered", "user_id": str(result.inserted_id)}

# @app.post("/login", response_model=Token)
# async def login(form_data: OAuth2PasswordRequestForm = Depends()):
#     user = users_collection.find_one({"email": form_data.username})
#     if not user or not verify_password(form_data.password, user["password"]):
#         raise HTTPException(status_code=400, detail="Incorrect email or password")
    
#     access_token = create_access_token(data={"sub": str(user["_id"])})
#     return {"access_token": access_token, "token_type": "bearer"}

# @app.post("/account")
# async def create_account(account: Account, current_user: str = Depends(get_current_user)):
#     if current_user != account.user_id:
#         raise HTTPException(status_code=403, detail="Not authorized")
    
#     # Generate unique account number (simple: timestamp + random)
#     import random
#     account_number = f"ACCT-{int(datetime.now().timestamp())}-{random.randint(1000, 9999)}"
    
#     account_data = {
#         "user_id": account.user_id,
#         "account_number": account_number,
#         "balance": 500,  # Initial deposit
#         "acc_type": account.acc_type
#     }
#     result = accounts_collection.insert_one(account_data)
    
#     # Create initial transaction
#     transactions_collection.insert_one({
#         "from_account": "INITIAL_DEPOSIT",
#         "to_account": account_number,
#         "amount": 500,
#         "timestamp": datetime.now()
#     })
    
#     return {"message": "Account created", "account_id": str(result.inserted_id)}

# @app.get("/dashboard/{user_id}")
# async def get_dashboard(user_id: str, current_user: str = Depends(get_current_user)):
#     if current_user != user_id:
#         raise HTTPException(status_code=403, detail="Not authorized")
    
#     accounts = list(accounts_collection.find({"user_id": user_id}, {"_id": 0}))
#     transactions = list(transactions_collection.find({
#         "$or": [{"from_account": {"$in": [acc["account_number"] for acc in accounts]}},
#                 {"to_account": {"$in": [acc["account_number"] for acc in accounts]}}]
#     }, {"_id": 0}))
    
#     return {"accounts": accounts, "transactions": transactions}