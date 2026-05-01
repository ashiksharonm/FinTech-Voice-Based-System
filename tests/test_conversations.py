import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import app, get_db
from backend.database import Base

# Setup Test Database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_conversations.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def run_around_tests():
    # Setup before each test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    # Teardown
    pass

def test_initial_chat_creates_session():
    # Note: Requires OPENAI_API_KEY environment variable set during test execution
    response = client.post("/chat", json={"message": "Hi, I am looking for debt."})
    
    # If API key is missing, it returns the fallback error message, but still 200 OK
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "response" in data

def test_analytics_endpoint_empty():
    response = client.get("/analytics")
    assert response.status_code == 200
    data = response.json()
    assert data["total_sessions"] == 0
    assert data["completed_sessions"] == 0
