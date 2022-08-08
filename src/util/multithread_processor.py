
from ast import Call
from concurrent.futures import thread
from math import ceil
import threading
from typing import Callable, Optional


class MultithreadProcessor(object):
  def __init__(self, data_to_process: list, processor: Callable, thread_count: int) -> None:
    self.thread_count: int = min(thread_count, len(data_to_process))
    self.data_to_process: list = data_to_process
    self.processor: Callable[[list], list] = processor

  def run_and_aggregrate(self) -> list:
    result = []
    def thread_func(*args):
      r = self.processor(*args)
      result.extend(r)

    threads = []
    num_data = len(self.data_to_process)
    chunk_size = ceil((num_data * 1.0) / self.thread_count)
    
    for t_id in range(self.thread_count):
      chunk_index = chunk_size * t_id
      chunk = self.data_to_process[chunk_index: chunk_index + chunk_size]
      if chunk:
        t = threading.Thread(target=thread_func, args=[chunk])
        t.start()
        threads.append(t)
    
    for t in threads:
      t.join()

    return result
