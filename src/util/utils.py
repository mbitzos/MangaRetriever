
import dataclasses
import json


class JSONSerializableDataclass:
  def __str__(self) -> str:
    return json.dumps(dataclasses.asdict(self))