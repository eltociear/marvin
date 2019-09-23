# Slack Slash Commands

## Requests
Slack sends slash commands as a url-encoded payload. To build a new slash command, set up a request handler like this:

```python
from starlette.requests import Request
from starlett.response import Response


async def my_handler(request: Request) -> Response:
    # payload is a dict
    payload = await request.form()
    user = payload.get("user_name")

    #return an (optionally empty) response
    return Response(f"Thanks {user}!")
```
