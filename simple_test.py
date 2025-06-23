import requests
import json

def test_simple():
    try:
        # 测试健康检查
        response = requests.get("http://localhost:5000/health")
        print(f"Health check: {response.status_code} - {response.text}")
        
        # 测试ASR端点
        data = {"text": "test"}
        response = requests.post("http://localhost:5000/asr", json=data)
        print(f"ASR test: {response.status_code} - {response.text}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_simple()
