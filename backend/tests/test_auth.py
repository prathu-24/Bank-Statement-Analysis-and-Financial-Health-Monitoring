import pytest
from app.routes.auth import (
    login, get_current_user, require_authenticated_user,
    create_access_token, decode_access_token,
    LoginRequest, DEMO_USERS
)
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

def test_login_demo_judge_success():
    req = LoginRequest(
        email="judge@finsight.local",
        password="JudgePassword2024!"
    )
    res = login(req)
    assert res["status"] == "success"
    assert "access_token" in res
    assert res["token_type"] == "bearer"
    assert res["user"]["name"] == "Hackathon Judge"
    assert res["user"]["role"] == "Auditor & Evaluator"
    assert res["user"]["email"] == "judge@finsight.local"

    # Verify decoded JWT payload
    payload = decode_access_token(res["access_token"])
    assert payload["sub"] == "judge@finsight.local"
    assert payload["role"] == "Auditor & Evaluator"
    assert "exp" in payload

def test_login_demo_wrong_password_fails():
    req = LoginRequest(
        email="judge@finsight.local",
        password="WrongPassword123"
    )
    with pytest.raises(HTTPException) as exc:
        login(req)
    assert exc.value.status_code == 401
    assert "Invalid password" in exc.value.detail

def test_login_custom_user_and_password_verification():
    req = LoginRequest(
        email="auditor.specialist@bank.com",
        password="InitialPassword2024!"
    )
    res = login(req)
    assert res["status"] == "success"
    assert res["user"]["email"] == "auditor.specialist@bank.com"

    # Subsequent login with correct password succeeds
    res_again = login(req)
    assert res_again["status"] == "success"

    # Subsequent login with wrong password fails
    bad_req = LoginRequest(
        email="auditor.specialist@bank.com",
        password="DifferentPassword"
    )
    with pytest.raises(HTTPException) as exc:
        login(bad_req)
    assert exc.value.status_code == 401

def test_login_empty_credentials():
    req = LoginRequest(email="", password="")
    with pytest.raises(HTTPException) as exc_info:
        login(req)
    assert exc_info.value.status_code == 400

def test_jwt_tampering_rejected():
    token = create_access_token({"sub": "legit@finsight.local"})
    tampered_token = token[:-5] + "ABCDE"
    with pytest.raises(HTTPException) as exc:
        decode_access_token(tampered_token)
    assert exc.value.status_code == 401

def test_require_authenticated_user_dependency():
    token = create_access_token({"sub": "judge@finsight.local", "name": "Judge"})
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    user = require_authenticated_user(creds)
    assert user["sub"] == "judge@finsight.local"

    # Missing creds raises 401
    with pytest.raises(HTTPException) as exc:
        require_authenticated_user(None)
    assert exc.value.status_code == 401

def test_current_user_status():
    user_payload = {"sub": "judge@finsight.local", "name": "Hackathon Judge"}
    res = get_current_user(user=user_payload)
    assert res["authenticated"] is True
    assert res["user"]["sub"] == "judge@finsight.local"
