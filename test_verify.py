import requests

# Test the verify endpoint
try:
    response = requests.get("http://localhost:8001/verify")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
