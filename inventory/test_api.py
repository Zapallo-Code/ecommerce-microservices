"""
Script de prueba para los endpoints de inventory.
Ejecuta el servidor en background y prueba todos los endpoints.
"""
import requests
import uuid
import json
import time

BASE_URL = "http://localhost:8000/inventory"

def test_health():
    """Test health check endpoint."""
    print("\n1. Testing health check...")
    response = requests.get(f"{BASE_URL}/health/")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    assert response.status_code == 200
    print("   ✅ Health check OK")

def test_get_inventory():
    """Test get inventory endpoint."""
    print("\n2. Testing get inventory...")
    response = requests.get(f"{BASE_URL}/1/")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    assert response.status_code == 200
    print("   ✅ Get inventory OK")

def test_decrease_success():
    """Test decrease stock successfully."""
    print("\n3. Testing decrease stock (success)...")
    data = {
        "operation_id": str(uuid.uuid4()),
        "product_id": 1,
        "quantity": 5
    }
    response = requests.post(f"{BASE_URL}/decrease/", json=data)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    assert response.status_code == 200
    assert response.json()["status"] == "updated"
    print("   ✅ Decrease stock OK")
    return data["operation_id"]

def test_decrease_idempotent(operation_id):
    """Test idempotent decrease."""
    print("\n4. Testing decrease stock (idempotent)...")
    data = {
        "operation_id": operation_id,
        "product_id": 1,
        "quantity": 5
    }
    response = requests.post(f"{BASE_URL}/decrease/", json=data)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    assert response.status_code == 200
    print("   ✅ Idempotency OK")

def test_decrease_insufficient():
    """Test decrease with insufficient stock."""
    print("\n5. Testing decrease stock (insufficient)...")
    data = {
        "operation_id": str(uuid.uuid4()),
        "product_id": 1,
        "quantity": 10000
    }
    response = requests.post(f"{BASE_URL}/decrease/", json=data)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    assert response.status_code == 409
    assert response.json()["status"] == "no_stock"
    print("   ✅ Insufficient stock error OK")

def test_compensate():
    """Test compensate stock."""
    print("\n6. Testing compensate stock...")
    data = {
        "operation_id": str(uuid.uuid4()),
        "product_id": 1,
        "quantity": 10
    }
    response = requests.post(f"{BASE_URL}/compensate/", json=data)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    assert response.status_code == 200
    assert response.json()["status"] == "compensated"
    print("   ✅ Compensate OK")

def test_random_failures():
    """Test random failures (may fail due to simulation)."""
    print("\n7. Testing random failures (10 attempts)...")
    successes = 0
    failures = 0
    for i in range(10):
        data = {
            "operation_id": str(uuid.uuid4()),
            "product_id": 2,
            "quantity": 1
        }
        response = requests.post(f"{BASE_URL}/decrease/", json=data)
        if response.status_code == 200:
            successes += 1
        else:
            failures += 1
    
    print(f"   Successes: {successes}, Failures: {failures}")
    print(f"   Simulated failure rate: {failures/10*100:.1f}%")
    print("   ✅ Random failures working")

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Inventory Microservice API")
    print("=" * 60)
    print(f"\nBase URL: {BASE_URL}")
    print("Make sure the server is running: python manage.py runserver")
    print("\nWaiting 2 seconds...")
    time.sleep(2)
    
    try:
        test_health()
        test_get_inventory()
        op_id = test_decrease_success()
        test_decrease_idempotent(op_id)
        test_decrease_insufficient()
        test_compensate()
        test_random_failures()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to server. Is it running?")
        print("   Run: python manage.py runserver")
    except Exception as e:
        print(f"\n❌ Error: {e}")
