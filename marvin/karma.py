import google.cloud.firestore

client = google.cloud.firestore.Client(project="prefect-marvin")


def update_karma(regex_match):
    votes = {"++": 1, "--": -1}
    subject, vote, reason = regex_match.groups()
    collection = client.collection("karma")

    karma_target = collection.document(document_id=subject).get()
    if karma_target.exists:
        value = karma_target.get("value", 0)
        new_value = value + votes[vote]
        karma_target.reference.update({"value": new_value})
        return f"{subject} has {new_value} points"
    else:
        collection.add(document_id=subject, document_data={"value": votes[vote]})
        return f"{subject} has {votes[vote]} points"
