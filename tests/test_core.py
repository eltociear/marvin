import hmac

import pytest


@pytest.mark.parametrize("endpoint", ["/", "/standup"])
async def test_token_authentication_prevents_requests_json(app, endpoint):
    with pytest.raises(AssertionError):
        await app.post(endpoint, json={"token": "None-provided"})


@pytest.mark.parametrize("endpoint", ["/", "/standup"])
async def test_token_authentication_prevents_requests_data(app, endpoint):
    with pytest.raises(AssertionError):
        await app.post(endpoint, data="token=None-provided")


async def test_secret_authentication_prevents_requests(app):
    payload = b"{}"
    headers = {"x-hub-signature": "sha1=bb7"}
    with pytest.raises(AssertionError) as exc:
        await app.post("/", data=payload, headers=headers)
    assert "Secret" in str(exc.value)


async def test_secret_authentication_works(app, secret):
    payload = b"{}"
    encrypted = hmac.new(secret, msg=payload, digestmod="sha1").hexdigest()
    headers = {"x-hub-signature": f"sha1={encrypted}"}
    await app.post("/", data=payload, headers=headers)


async def test_token_authentication_works(app, token):
    await app.post("/", json={"token": token})


async def test_url_verification(app, token):
    r = await app.post(
        "/", json={"token": token, "challenge": "yy", "type": "url_verification"}
    )
    assert r.ok
    assert r.json()["challenge"] == "yy"


async def test_healthcheck(app):
    r = await app.get("/healthcheck")
    assert r.ok
