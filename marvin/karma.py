import google.cloud.firestore

client = google.cloud.firestore.Client(project="prefect-marvin")


def update_karma(regex_match):
    groups = regex_match.groups()
    collection = client.collection(u"karma")

    try:
      karma_target = collection.document(document_id=groups[0]).get()
      value = karma_target.get("value")
      if groups[1] == "++":
        karma_target.update({
          "value": value += 1
        })
      elif groups[1] == "--":
        karma_target.update({
          "value": value -= 1
        })
      return f"{group[0]} has {value} points"
    except google.cloud.exceptions.NotFound:
      if groups[1] == "++":
        value = 1
        new_karma_target = {"value": value}
      elif groups[1] == "--":
        value = -1
        new_karma_target = {"value": value}

      collection.add(document_id=groups[0], document_data=new_karma_target)
      
      return f"{group[0]} has {value} points
