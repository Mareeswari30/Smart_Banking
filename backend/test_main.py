import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app, Base, get_db  


DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)



def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_and_teardown_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)



# TESTS

def test_register_user():
    """Test registering a user with a sample image file"""
    response = client.post(
        "/register",
        data={
            "name": "Mareeswari",
            "email": "marees2@gmail.com",
            "password": "Marees@12",
            "mobile_number": "+919876543210",
        },
        files=[
            ("documents", ("my_aadhar.jpg", b"fake image bytes", "image/jpeg")),
        ],
    )

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "User registered"
    assert "user_id" in data


def test_login_user():
    """Test logging in after registration"""
  
    client.post(
        "/register",
        data={
            "name": "Mareeswari",
            "email": "marees_login@gmail.com",
            "password": "Marees@12",
            "mobile_number": "+919876543210",
        },
    )


    response = client.post(
        "/login",
        data={
            "username": "marees_login@gmail.com",
            "password": "Marees@12",
            "grant_type": "password", 
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 200
    json_data = response.json()
    assert "access_token" in json_data
    assert json_data["token_type"] == "bearer"


def test_create_account():
    """Test account creation after login"""
 
    client.post(
        "/register",
        data={
            "name": "Mareeswari",
            "email": "marees_account@gmail.com",
            "password": "Marees@12",
            "mobile_number": "+919876543210",
        },
    )

    login_response = client.post(
        "/login",
        data={
            "username": "marees_account@gmail.com",
            "password": "Marees@12",
            "grant_type": "password",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = login_response.json()["access_token"]

    
    response = client.post(
        "/account",
        json={"user_id": "1", "acc_type": "savings"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Account created"
    assert "account_id" in data


def test_dashboard():
    """Test dashboard retrieval after creating account"""
    
    client.post(
        "/register",
        data={
            "name": "Mareeswari",
            "email": "marees_dashboard@gmail.com",
            "password": "Marees@12",
            "mobile_number": "+919876543210",
        },
    )

    login_response = client.post(
        "/login",
        data={
            "username": "marees_dashboard@gmail.com",
            "password": "Marees@12",
            "grant_type": "password",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = login_response.json()["access_token"]

   
    client.post(
        "/account",
        json={"user_id": "1", "acc_type": "savings"},
        headers={"Authorization": f"Bearer {token}"},
    )

    
    response = client.get(
        "/dashboard/1",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "accounts" in data
    assert isinstance(data["accounts"], list)
    assert "transactions" in data
    assert isinstance(data["transactions"], list)
