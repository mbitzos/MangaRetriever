from src.fetchers.indigo import IndigoRetriever
from src.util.recorder import MangaDataRecorder


recorder = MangaDataRecorder("indigo")
indigoRetriever = IndigoRetriever(recorder)

manga, metadata = indigoRetriever.get_manga(ignore_cache=True)

print (f"Total manga fetched: {len(manga)}")
print (f"Total discounted manga: {len(manga.get_discounted())}")
print("REQUEST METADATA:")
print(metadata)
