import requests
import sys

URL = "http://localhost:8000/api/analyze"
TEXT = "Este email é um teste. Por favor ignore."

def test_api():
    print(f"Testing {URL} with text: {TEXT}")
    try:
        response = requests.post(URL, data={"text_input": TEXT})
        print(f"Status Code: {response.status_code}")
        print("Response Body:")
        print(response.text)
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_api()
