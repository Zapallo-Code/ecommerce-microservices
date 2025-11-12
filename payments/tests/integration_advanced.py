"""
Advanced integration test script for payments API endpoints.
Uses requests library for HTTP testing.

Requirements:
    pip install requests  OR  uv pip install requests

Run this after starting the server:
    Terminal 1: python manage.py runserver 8002
    Terminal 2: python -m tests.integration_advanced
"""
import requests
import json

BASE_URL = "http://localhost:8002"


def test_process_payment():
    """Test POST /payments endpoint"""
    print("\n" + "="*60)
    print("TEST 1: Process Payment")
    print("="*60)
    
    payload = {
        "user_id": "user_test_123",
        "amount": 1500.50,
        "product_id": "product_abc_456"
    }
    
    print(f"\n📤 Request:")
    print(f"POST {BASE_URL}/payments/")
    print(f"Body: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(f"{BASE_URL}/payments/", json=payload)
        print(f"\n📥 Response ({response.status_code}):")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 200:
            print("\n✅ Payment processed successfully")
            return response.json().get("payment_id")
        elif response.status_code == 409:
            print("\n⚠️ Payment processing error (expected - random failure)")
            return response.json().get("payment_id")
        else:
            print(f"\n❌ Unexpected error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"\n❌ Connection error: {e}")
        return None


def test_refund_payment(payment_id):
    """Test POST /payments/{payment_id}/refund/ endpoint"""
    print("\n" + "="*60)
    print("TEST 2: Refund Payment")
    print("="*60)
    
    if not payment_id:
        print("\n⚠️ No payment_id to refund (skipping test)")
        return
    
    payload = {
        "reason": "Transaction failed in orchestrator"
    }
    
    print(f"\n📤 Request:")
    print(f"POST {BASE_URL}/payments/{payment_id}/refund/")
    print(f"Body: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/payments/{payment_id}/refund/",
            json=payload
        )
        print(f"\n📥 Response ({response.status_code}):")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 200:
            print("\n✅ Payment refunded successfully")
        else:
            print(f"\n❌ Unexpected error: {response.status_code}")
            
    except Exception as e:
        print(f"\n❌ Connection error: {e}")


def test_health_check():
    """Test health check endpoint (if available)"""
    print("\n" + "="*60)
    print("TEST 0: Health Check")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/health/")
        print(f"\n📥 Response ({response.status_code}):")
        
        if response.status_code == 404:
            print("⚠️ Health endpoint not implemented (404)")
            return True  # Continue tests anyway
        
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 200:
            print("\n✅ Service running correctly")
            return True
        else:
            print(f"\n❌ Service not healthy")
            return False
            
    except Exception as e:
        print(f"\n❌ Connection error: {e}")
        print("\n⚠️ Make sure the service is running:")
        print("   python manage.py runserver 8002")
        return False


def main():
    print("\n" + "🧪"*30)
    print("PAYMENTS MICROSERVICE INTEGRATION TESTS")
    print("🧪"*30)
    
    # Test 0: Health check (optional)
    health_ok = test_health_check()
    
    # Test 1: Process payment
    payment_id = test_process_payment()
    
    # Test 2: Refund payment (if payment_id obtained)
    if payment_id:
        test_refund_payment(payment_id)
    
    # Test 3: Create another payment to test randomness
    print("\n" + "="*60)
    print("TEST 3: Process Another Payment (Test Randomness)")
    print("="*60)
    test_process_payment()
    
    print("\n" + "="*60)
    print("TESTS COMPLETED")
    print("="*60)
    print("\n📝 Verify that:")
    print("  ✅ POST /payments/ accepts user_id, amount, product_id")
    print("  ✅ Response includes payment_id")
    print("  ✅ POST /payments/{id}/refund/ works correctly")
    print("  ✅ Refund always returns 200 OK (Saga idempotency)")
    print("  ✅ Random success/failure behavior works")
    print()


if __name__ == "__main__":
    main()
