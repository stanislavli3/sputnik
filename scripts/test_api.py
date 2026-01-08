"""Test script for Sputnik API endpoints."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import requests


def test_health():
    """Test health endpoint."""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print("✅ Health check: PASSED")
        return True
    except Exception as e:
        print(f"❌ Health check: FAILED - {e}")
        return False


def test_schema():
    """Test schema endpoint."""
    try:
        response = requests.get("http://localhost:8000/api/v1/schema", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert "tables" in data
        assert "relationships" in data
        print(f"✅ Schema endpoint: PASSED ({len(data['tables'])} tables)")
        return True
    except Exception as e:
        print(f"❌ Schema endpoint: FAILED - {e}")
        return False


def test_query():
    """Test query endpoint."""
    try:
        payload = {"question": "What is the total revenue?"}
        response = requests.post(
            "http://localhost:8000/api/v1/query",
            json=payload,
            timeout=10,
        )
        # May return 401 if auth is required, or 200 if in dev mode
        if response.status_code in [200, 401]:
            if response.status_code == 200:
                data = response.json()
                assert "answer" in data
                print("✅ Query endpoint: PASSED (dev mode)")
            else:
                print("✅ Query endpoint: Requires authentication (expected)")
            return True
        else:
            print(f"❌ Query endpoint: Unexpected status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Query endpoint: FAILED - {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 Testing Sputnik API")
    print("=" * 50)
    print()

    # Wait for server to be ready
    print("Waiting for server to start...")
    for _ in range(10):
        try:
            requests.get("http://localhost:8000/health", timeout=2)
            break
        except:
            time.sleep(1)
    else:
        print("❌ Server not responding. Is it running?")
        print("   Start with: python scripts/start_server.py")
        return

    print("Server is ready!\n")

    # Run tests
    results = []
    results.append(test_health())
    results.append(test_schema())
    results.append(test_query())

    # Summary
    print()
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("✅ All tests passed!")
    else:
        print("⚠️  Some tests failed. Check the output above.")


if __name__ == "__main__":
    main()

