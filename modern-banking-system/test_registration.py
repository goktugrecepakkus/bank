import requests
import uuid
import random

BASE_URL = "http://localhost:8000"

# Wait, if the server is not running, I can just use the FastAPI TestClient!
from fastapi.testclient import TestClient
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from backend.main import app

client = TestClient(app)

def test_registration():
    username = f"testuser_{random.randint(1000, 9999)}"
    national_id = f"{random.randint(100000000, 999999999)}"
    
    # 1. Create Customer
    customer_data = {
        "first_name": "Test",
        "last_name": "User",
        "national_id": national_id,
        "phone_number": "1234567890",
        "address": "123 Test St",
        "username": username,
        "password": "password123",
        "mothers_maiden_name": "Smith",
        "role": "customer"
    }
    print("Creating customer...")
    res_customer = client.post("/api/customers/", json=customer_data)
    print("Customer res:", res_customer.status_code, res_customer.text)
    
    if res_customer.status_code != 201:
        print("Failed to create customer")
        return
        
    customer_id = res_customer.json()["id"]
    
    # 2. Create Account
    account_data = {
        "customer_id": customer_id,
        "account_type": "CHECKING"
    }
    
    print("Creating account...")
    res_account = client.post("/api/accounts/", json=account_data)
    print("Account res:", res_account.status_code, res_account.text)

if __name__ == "__main__":
    test_registration()
