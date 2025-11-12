"""
Simple integration test script for payments API endpoints.
Uses urllib (no external dependencies required).

Run this after starting the server:
    Terminal 1: python manage.py runserver 8002
    Terminal 2: python -m tests.integration_simple
"""
import urllib.request
import json
import sys

def test_create_payment():
    """Test POST /payments/"""
    print("=" * 60)
    print("Test 1: POST /payments/ - Create Payment")
    print("=" * 60)
    
    url = "http://127.0.0.1:8002/payments/"
    data = {
        "user_id": "USER-TEST-001",
        "amount": 1500.50,
        "product_id": "PROD-TEST-001"
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            status = response.status
            result = json.loads(response.read().decode('utf-8'))
            
            print(f"\n✓ Status Code: {status}")
            print(f"✓ Response:")
            print(json.dumps(result, indent=2))
            
            return result.get('payment_id')
            
    except urllib.error.HTTPError as e:
        status = e.code
        try:
            error_body = json.loads(e.read().decode('utf-8'))
            print(f"\n✗ Status Code: {status}")
            print(f"✗ Error Response:")
            print(json.dumps(error_body, indent=2))
        except:
            print(f"\n✗ Status Code: {status}")
            print(f"✗ Error: {e.read().decode('utf-8')}")
        return None
    except Exception as e:
        print(f"\n✗ Connection Error: {e}")
        print("Make sure the server is running on port 8002")
        return None

def test_refund_payment(payment_id):
    """Test POST /payments/{id}/refund/"""
    print("\n" + "=" * 60)
    print(f"Test 2: POST /payments/{payment_id}/refund/ - Refund Payment")
    print("=" * 60)
    
    url = f"http://127.0.0.1:8002/payments/{payment_id}/refund/"
    data = {
        "reason": "Customer requested refund - Test"
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            status = response.status
            result = json.loads(response.read().decode('utf-8'))
            
            print(f"\n✓ Status Code: {status}")
            print(f"✓ Response:")
            print(json.dumps(result, indent=2))
            
    except urllib.error.HTTPError as e:
        status = e.code
        try:
            error_body = json.loads(e.read().decode('utf-8'))
            print(f"\n✗ Status Code: {status}")
            print(f"✗ Error Response:")
            print(json.dumps(error_body, indent=2))
        except:
            print(f"\n✗ Status Code: {status}")
            print(f"✗ Error: {e.read().decode('utf-8')}")
    except Exception as e:
        print(f"\n✗ Connection Error: {e}")

if __name__ == "__main__":
    print("\n" + "🧪 PAYMENT API INTEGRATION TESTS".center(60) + "\n")
    
    # Test 1: Create payment
    payment_id = test_create_payment()
    
    if payment_id:
        # Test 2: Refund the payment
        test_refund_payment(payment_id)
    else:
        print("\n⚠ Skipping refund test - payment creation failed")
    
    # Test 3: Create another payment to test random success/failure
    print("\n" + "=" * 60)
    print("Test 3: POST /payments/ - Create Second Payment (Test Randomness)")
    print("=" * 60)
    test_create_payment()
    
    print("\n" + "=" * 60)
    print("✓ Tests completed!")
    print("=" * 60 + "\n")
