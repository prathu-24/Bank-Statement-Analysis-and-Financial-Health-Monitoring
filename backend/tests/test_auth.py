import pytest
from app.routes.auth import login, get_current_user, LoginRequest
from fastapi import HTTPException

def test_login_demo_judge_success():
    req = LoginRequest(
        email="judge@finsight.local",
        password="JudgePassword2024!"
    )
    res = login(req)
    assert res["status"] == "success"
    assert "access_token" in res
    assert res["user"]["name"] == "Hackathon Judge"
    assert res["user"]["role"] == "Auditor & Evaluator"
    assert res["user"]["email"] == "judge@finsight.local"

def test_login_custom_user():
    req = LoginRequest(
        email="custom.auditor@firm.com",
        password="Password123"
    )
    res = login(req)
    assert res["status"] == "success"
    assert res["user"]["name"] == "Custom Auditor"
    assert res["user"]["email"] == "custom.auditor@firm.com"

def test_login_empty_credentials():
    req = LoginRequest(email="", password="")
    with pytest.raises(HTTPException) as exc_info:
        login(req)
    assert exc_info.value.status_code == 400

def test_current_user_status():
    res = get_current_user()
    assert res["authenticated"] is True
    assert "default_user" in res
