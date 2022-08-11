from abc import abstractmethod, ABC
from collections import defaultdict
import dataclasses
from multiprocessing.pool import INIT
from random import randint, random
import re
import time
from tkinter.tix import MAX
from turtle import back
from typing import Any, Optional

import requests

from src.models import MangaCollection
from src.util import recorder
from src.util.recorder import MangaDataRecorder
from src.util.utils import JSONSerializableDataclass


MAX_RETRIES = 3
INITIAL_RETRY_TIMEOUT_S = 1
RETRY_BACKOFF_MUL = 1.5
@dataclasses.dataclass
class FetchMetaData(JSONSerializableDataclass):
  cached: bool
  num_request_made: Optional[int] = None
  total_request_time_s: Optional[int] = None # in seconds
  avg_request_time_ms: Optional[float] = None  # in ms
  total_failed_requests: Optional[int] = 0
  dynamic_data: dict = dataclasses.field(default_factory=lambda: {})
  failed_request_code_map: Optional[dict] = dataclasses.field(default_factory=lambda: {})

class MangaFetcher(ABC):
  @dataclasses.dataclass
  class MetaData:
    total_requests: int = 0
    total_request_time: int = 0 # in ns
    total_failed_requests: int = 0
    failed_request_code_map: dict = dataclasses.field(default_factory=lambda: defaultdict(int))
    dynamic_data: dict = dataclasses.field(default_factory=lambda: {})

  def __init__(self, recorder: MangaDataRecorder) -> None:
    self.recorder = recorder
    self._metadata = self.MetaData()
  
  @abstractmethod
  def _get_manga(self) -> MangaCollection:
    raise NotImplementedError()
  
  def get_manga(self, write_to_disk=True, ignore_cache=False) -> tuple[MangaCollection, FetchMetaData]:
    """
    Gets manga data
    """
    if (write_to_disk or ignore_cache) and not self.recorder:
      raise Exception("Must provider a recorder!")
    
    # cache op
    if not ignore_cache:
      if cached_data:= self.recorder.read_today():
        print("Returning Cached data!")
        return MangaCollection(cached_data), FetchMetaData(cached=True)
    self._metadata = self.MetaData()

    # fetch real
    manga_data = self._get_manga()

    # meta data stuff
    total_requests = self._metadata.total_requests
    total_request_time = self._metadata.total_request_time / 1e6  # ns -> ms
    metadata =  FetchMetaData(
      cached=False,
      total_request_time_s=round(total_request_time / 1e3,2),  # in seconds
      avg_request_time_ms=0 if not total_requests else round(total_request_time / total_requests, 2),
      num_request_made=total_requests,
      total_failed_requests=self._metadata.total_failed_requests,
      failed_request_code_map=dict(self._metadata.failed_request_code_map),
      dynamic_data=self._metadata.dynamic_data,
    )

    # persist to disk
    if write_to_disk:
      self.recorder.write(manga_data, overwrite=True)
      self.recorder.write_metadata(metadata, overwrite=True)
    return manga_data, metadata

  def get_request(self, url: str, query_params: dict[str, Any], raise_error: bool =True) -> tuple[dict, int]:
    """
    performs a get requests
    """
    backoff = INITIAL_RETRY_TIMEOUT_S
    retries = MAX_RETRIES
    while retries > 0:
      start = time.perf_counter_ns() 
      query_params_str = "&".join([f"{key}={value}" for key,value in query_params.items()])
      url =  f"{url}/?{query_params_str}"
      response = requests.get(url)
      end = time.perf_counter_ns()
      diff = (end-start)
      try:
        if raise_error:
          response.raise_for_status()
          if 'application/json' in response.headers.get('Content-Type'):
            content = response.json()
            self._metadata.total_requests += 1
            self._metadata.total_request_time += diff
            return content, response.status_code
          else:
              raise Exception("NOT_JSON")
      except Exception as e:
        pass
      retries -= 1
      time.sleep(backoff)
      backoff *= RETRY_BACKOFF_MUL
    
    self._metadata.total_requests += 1
    self._metadata.total_failed_requests += 1
    self._metadata.failed_request_code_map["MAX_RETRIES"] += 1
    print("Failed max retries")
    raise Exception("Failed: Max retries")


