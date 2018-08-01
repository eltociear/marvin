import pytest


@pytest.mark.parametrize("data_or_body", ["data", "json"])
@pytest.mark.parametrize("endpoint", ["/", "/standup"])
def test_token_authentication_prevents_requests(app, endpoint, data_or_body):
    with pytest.raises(AssertionError):
        app.post(endpoint, **{data_or_body: {"token": "None-provided"}})


def test_token_authentication_works(app, token):
    app.post("/", json={"token": token})


def test_url_verification(app, token):
    r = app.post(
        "/", json={"token": token, "challenge": "yy", "type": "url_verification"}
    )
    assert r.ok
    assert r.text == "yy"
