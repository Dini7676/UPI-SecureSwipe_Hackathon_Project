from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    r = client.get('/health')
    assert r.status_code == 200
    assert r.json()['status'] == 'ok'

def test_send_verify_otp_flow(monkeypatch):
    # Replace Redis with local dict via monkeypatch if needed; here use actual route
    mobile = '9999999999'
    r = client.post('/auth/send-otp', json={'mobile': mobile})
    assert r.status_code == 200
    otp = r.json()['otp_debug']
    r = client.post('/auth/verify-otp', json={'mobile': mobile, 'otp': otp})
    assert r.status_code == 200
    assert 'access_token' in r.json()
