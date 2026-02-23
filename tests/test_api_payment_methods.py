from tests.helpers import auth_header


def test_payment_method_create_list_and_delete_flow(client, user):
    headers = auth_header(user["token"])
    create_resp = client.post(
        "/api/payment-methods",
        headers=headers,
        json={"method_type": "Visa", "details": "****4242"},
    )
    assert create_resp.status_code == 201
    created = create_resp.get_json()
    assert created["is_active"] is True
    method_id = created["id"]

    list_resp = client.get("/api/payment-methods", headers=headers)
    assert list_resp.status_code == 200
    methods = list_resp.get_json()["data"]
    assert len(methods) == 1
    assert methods[0]["id"] == method_id

    delete_resp = client.delete(f"/api/payment-methods/{method_id}", headers=headers)
    assert delete_resp.status_code == 200
    assert delete_resp.get_json()["status"] == "archived"

    list_after = client.get("/api/payment-methods", headers=headers)
    assert list_after.status_code == 200
    assert list_after.get_json()["data"] == []
