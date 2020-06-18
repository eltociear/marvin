## Marvin
<p align="center">
<a href=https://circleci.com/gh/PrefectHQ/marvin/tree/master>
    <img src="https://circleci.com/gh/PrefectHQ/marvin/tree/master.svg?style=shield&circle-token=718689b37be2a34ff44dde84c8e0b0c8aa49fce2">
</a>

Don’t pretend you want to talk to me, I know you hate me.

### Introduction and Overview

Marvin is the official slackbot for Prefect and is a Genuine People Personality (GPP) prototype; he helps us organize daily updates,
test out deployment infrastructures, and other mundane tasks (we haven't found a convincing use of his vast computing power yet, and we suspect this has led to a certain level of ennui with Marvin).

### Requirements
Marvin requires Python 3.7+

To install for development:
```
git clone https://www.github.com/prefecthq/marvin.git
pip install -e marvin
```

Then watch the magic:
```
marvin
```

### How Marvin works

Marvin, at his core, is a simple webserver running on [apistar](https://github.com/encode/apistar) and [uvicorn](https://github.com/encode/uvicorn). He is subscribed to certain Slack Events and can proactively perform tasks as well by attaching them to the `asyncio` event loop the webserver is running.

Because Marvin's subscribed events are sent to a fixed IP address, local development can be tricky.  Using the functions provided in `marvin.utilities`, certain proactive API endpoints can be run (such as `channels.list`), but in order to spin up a fully functioning local deployment you'll need to do a few things:
- make sure you have Marvin's Slack tokens stored as an environment variable on your local machine
- after installing Marvin locally, start up the webserver with the CLI command `marvin`.  You should get immediate feedback, e.g.,
```
2018-08-20 09:22:11 DEBUG: Using selector: KqueueSelector
2018-08-20 09:22:11 INFO: New asyncio event loop created
2018-08-20 09:22:11 INFO: Started server process [56621]
2018-08-20 09:22:11 INFO: Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
```
- using [`ngrok`](https://ngrok.com/), create a temporary web address that forwards to Marvin (e.g., `ngrok http 8080`)
- update the [event subscriptions address](https://api.slack.com/apps/ABE7E2927/event-subscriptions?) to point to your local installation (**Note:** Doing this will effectively take Marvin offline, do it sparingly and make sure to update the address when you're done!)

#### Deployment

Marvin is deployed via Google Cloud Platform, Kubernetes and Docker.

### Contributing to Marvin


