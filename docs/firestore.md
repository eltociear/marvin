# Firestore

Marvin uses Firestore for stateful storage.

## Collections

`users`: Information about Prefect users. Each document contains the following fields:

- `name`: the user's name
- `email`: the user's Prefect email
- `slack`: the user's Slack ID
- `github`: the user's GitHub username
- `notion`: the user's Notion username
