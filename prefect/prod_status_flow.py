import docker
import os
import prefect
from prefect import Flow, Parameter, task
from prefect.triggers import always_run
from prefect.engine.signals import FAIL
from prefect.engine.state import Submitted, Running, Success
from prefect.environments.storage import Docker
from prefect.schedules import IntervalSchedule

import datetime
import json
import pendulum
import requests
import urllib.parse
import urllib.request


API_ID = os.getenv("STATUSIO_API_ID")
API_KEY = os.getenv("STATUSIO_API_KEY")
PROD_TOKEN = os.getenv("PROD_TOKEN")


class ProdAPIError(Exception):
    pass


def query(query: str, variables: dict = None):
    payload = dict(query=query)
    if variables:
        payload.update(variables=json.dumps(variables))

    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request("https://api.prefect.io/graphql", data=data)
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", "Bearer {}".format(PROD_TOKEN))

    # make request
    try:
        resp = urllib.request.urlopen(req)
        resp_data = json.loads(resp.read().decode())
        if "errors" in resp_data:
            raise ValueError(resp_data["errors"])
        return resp_data
    except Exception as exc:
        if "AuthenticationError" in str(exc):
            raise exc
        raise ProdAPIError(f"Possible issue with Prod: {repr(exc)}")


flow_id = Parameter("flow_id", default="bc9495b5-368b-4ba4-b238-cfaee534b11e")


@task
def interact_with_api(flow_id):
    # create a flow run in prod
    create_mutation = """
    mutation($input: create_flow_run_input!){
        create_flow_run(input: $input){
            id
        }
    }
    """
    flow_run = query(create_mutation, variables=dict(input=dict(flow_id=flow_id)))
    flow_run_id = flow_run["data"]["create_flow_run"]["id"]

    set_flow_run_state = """
    mutation($input: set_flow_run_states_input!){
        set_flow_run_states(input: $input){
            states{message}
        }
    }
    """

    running_id = prefect.context.get("flow_run_id", "unknown")

    # submit flow run
    variables = dict(
        input=dict(
            states=[
                dict(
                    state=Submitted(
                        f"Submitted by {running_id} in staging."
                    ).serialize(),
                    flow_run_id=flow_run_id,
                )
            ],
        )
    )
    query(set_flow_run_state, variables=variables)

    # run flow run
    variables = dict(
        input=dict(
            states=[
                dict(
                    state=Running(f"Dummy run by {running_id} in staging.").serialize(),
                    flow_run_id=flow_run_id,
                )
            ],
        )
    )
    query(set_flow_run_state, variables=variables)

    # finish flow run
    variables = dict(
        input=dict(
            states=[
                dict(
                    state=Success(f"Completed by {running_id} in staging.").serialize(),
                    flow_run_id=flow_run_id,
                )
            ],
        )
    )
    query(set_flow_run_state, variables=variables)


set_schedule_inactive = """
mutation($input: set_schedule_inactive_input!){
    set_schedule_inactive(input: $input){
        success
    }
}
"""


@task(trigger=always_run)
def update_status_io(payload):
    # deferred import so that the registering environment doesn't need to install
    # this package
    import statusio

    if not payload:
        prefect.context.logger.info("Received None for payload, assuming success!")
        return
    if isinstance(payload, ProdAPIError):
        prefect.context.logger.error(f"Possible issue with Prod: {repr(payload)}")
        api = statusio.Api(api_id=API_ID, api_key=API_KEY,)
        resp = api.IncidentCreate(
            statuspage_id="5f33ff702715c204c20d6da1",
            infrastructure_affected=[
                "5f33ff702715c204c20d6db1-5f33ff702715c204c20d6db0"
            ],
            incident_name="api-" + pendulum.now("utc").strftime("%Y-%m-%d-%H:%M"),
            incident_details="This is an automated incident report - the Prefect team will investigate and update shortly.",
            current_status=100,
            current_state=100,
        )

        # pause the schedule for this flow
        from prefect import Client

        c = Client()
        c.graphql(
            set_schedule_inactive,
            variables=dict(input={"flow_id": prefect.context.get("flow_id")}),
        )

        raise FAIL(f"StatusIO updated: {resp}")
    else:
        prefect.context.logger.warning(
            f"Received {repr(payload)} for payload - I won't assume the worst but someone should check."
        )
        # still fail to trigger an alert
        raise FAIL(
            f"Unexpectedly received {repr(payload)} response from previous task."
        )


schedule = IntervalSchedule(interval=datetime.timedelta(minutes=1.25))


with Flow("Prod Status", schedule=schedule) as flow:
    uptime_check = update_status_io(interact_with_api(flow_id))


if __name__ == "__main__":
    default_client = docker.from_env()
    storage = Docker(
        base_url=default_client.api.base_url,
        tls_config=docker.TLSConfig(default_client.api.cert),
        registry_url="gcr.io/prefect-tenant-0c5400/flows/",
        python_dependencies=["statusio-python"],
        env_vars={
            "STATUSIO_API_KEY": API_KEY,
            "STATUSIO_API_ID": API_ID,
            "PROD_TOKEN": PROD_TOKEN,
        },
    )
    flow.storage = storage
    flow.register("Marvin")
