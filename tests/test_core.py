import hmac
import pytest


@pytest.mark.parametrize("data_or_body", ["data", "json"])
@pytest.mark.parametrize("endpoint", ["/", "/standup"])
def test_token_authentication_prevents_requests(app, endpoint, data_or_body):
    with pytest.raises(AssertionError):
        app.post(endpoint, **{data_or_body: {"token": "None-provided"}})


def test_secret_authentication_prevents_requests(app):
    payload = b"{}"
    headers = {"x-hub-signature": "sha1=bb7"}
    with pytest.raises(AssertionError) as exc:
        app.post("/", data=payload, headers=headers)
    assert "Secret" in str(exc.value)


def test_secret_authentication_works(app, secret):
    payload = b"{}"
    encrypted = hmac.new(secret, msg=payload, digestmod="sha1").hexdigest()
    headers = {"x-hub-signature": f"sha1={encrypted}"}
    app.post("/", data=payload, headers=headers)


def test_token_authentication_works(app, token):
    app.post("/", json={"token": token})


def test_url_verification(app, token):
    r = app.post(
        "/", json={"token": token, "challenge": "yy", "type": "url_verification"}
    )
    assert r.ok
    assert r.text == "yy"
