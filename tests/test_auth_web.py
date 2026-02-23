def test_user_login_flow_creates_session(client, user):
    response = client.post(
        "/auth/login",
        data={"email": user["email"], "password": "secret123", "account_type": "user"},
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")
    with client.session_transaction() as session:
        assert session["role"] == "user"
        assert session["account_id"] == user["id"]


def test_provider_login_redirects_to_provider_dashboard(client, provider):
    response = client.post(
        "/auth/login",
        data={
            "email": provider["email"],
            "password": "verysecret",
            "account_type": "provider",
        },
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/provider/dashboard")
    with client.session_transaction() as session:
        assert session["role"] == "provider"
        assert session["account_id"] == provider["id"]
