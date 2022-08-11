from collections import defaultdict
import os
from src.fetchers.indigo import IndigoRetriever
from src.util.recorder import MangaDataRecorder


recorder = MangaDataRecorder("indigo")
indigoRetriever = IndigoRetriever(recorder)

manga, metadata = indigoRetriever.get_manga(ignore_cache=True)

print (f"Total manga fetched: {len(manga)}")
print (f"Total discounted manga: {len(manga.get_discounted())}")
print("REQUEST METADATA:")
print(metadata)

log_file = recorder.get_todays_file_name()
if os.path.exists(log_file):
  lines=open(log_file, "r+").readlines()
  import json
  pid_map :dict [str,int] = defaultdict(int)
  for line in lines:
    pid_map[json.loads(line)['id']]+= 1

  repeated_pids = [pid for pid,count in pid_map.items() if count > 1]
  print(f"# of unique pids: {len(pid_map.keys())}")
  print(f"# of repeated pids: {len(repeated_pids)}")
  print(f"Repeated pids: {repeated_pids}")