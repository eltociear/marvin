"""
This simple flow attempts to prompt a biweekly release by opening a PR from dev -> master every Monday.

If for any reason the PR fails to open, the Flow attempts to open an issue alerting the team, with
relevant debug information.
"""
import datetime
import pendulum

from prefect import Flow, task
from prefect.environments.kubernetes import DaskOnKubernetesEnvironment
from prefect.triggers import any_failed
from prefect.schedules import IntervalSchedule
from prefect.tasks.github import CreateGitHubPR, OpenGitHubIssue


pr_task = CreateGitHubPR(
    name="Open dev->master PR",
    repo="PrefectHQ/cloud",
    base="master",
    head="dev",
    title="Cloud Release",
    body="Autogenerated PR for the biweekly cloud release",
    max_retries=1,
    retry_delay=datetime.timedelta(minutes=1),
)


@task(trigger=any_failed)
def prepare_exception(exc):
    return repr(exc)


issue_task = OpenGitHubIssue(
    name="Open Release Issue",
    repo="PrefectHQ/cloud",
    title="Release Cycle is Broken",
    labels=["release", "bug"],
)


biweekly_schedule = IntervalSchedule(
    start_date=pendulum.parse("2019-03-11", tz="US/Eastern"),
    interval=datetime.timedelta(days=14),
)
env = DaskOnKubernetesEnvironment(
    base_image="python:3.6",
    registry_url="gcr.io/prefect-dev/flows/",
    python_dependencies=["dask_kubernetes", "kubernetes"],
)


with Flow(
    "Biweekly Cloud Release", environment=env, schedule=biweekly_schedule
) as flow:
    exc = prepare_exception(pr_task)  # will only run if pr_task fails in some way
    issue = issue_task(body=exc)


flow.set_reference_tasks([pr_task])
