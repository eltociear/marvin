import asyncio
import json
import os
import random
import requests
from concurrent.futures import ThreadPoolExecutor

from apistar.http import Body, Response


MARVIN_ACCESS_TOKEN = os.environ.get("MARVIN_ACCESS_TOKEN")


def create_issue(title, body, labels=None):
    url = "https://api.github.com/repos/PrefectHQ/prefect/issues"
    headers = {"AUTHORIZATION": f"token {MARVIN_ACCESS_TOKEN}"}
    issue = {"title": title, "body": body, "labels": labels or []}
    resp = requests.post(url, data=json.dumps(issue), headers=headers)
    if resp.status_code == 201:
        return Response("")


async def github_handler(data: Body):
    payload = json.loads(data)
    pr_data = payload.get("pull_request", {})
    labels = [lab.get("id", 0) for lab in pr_data.get("labels", [])]
    if 1163480691 in labels and payload.get("action") == "closed":
        was_merged = pr_data.get("merged", False)
        pr_link = pr_data.get("html_url")
        if was_merged and pr_link is not None:
            body = f"See {pr_link} for more details"
            return create_issue(
                title="Cloud PR references Core",
                body=body,
                labels=["cloud-integration-notification"],
            )
