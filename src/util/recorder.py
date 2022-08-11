from __future__ import annotations
import dataclasses
import datetime
from datetime import datetime
import typing
from dacite import Config, from_dict
import json

import os
from typing import Optional

if typing.TYPE_CHECKING:
  from src.fetchers.fetcher import FetchMetaData
from src.models import DiscountType, Manga


class MangaDataRecorder(object):
  def __init__(self, folder_location: str) -> None:
    self.folder_location = folder_location
    pass

  def get_todays_file_name(self) -> str:
    return self.get_log_file_name(datetime.today())

  def get_log_file_name(self, date: datetime) -> str:
    date_str = date.strftime("%d-%m-%Y")
    return f"data/{self.folder_location}/{date_str}.log"

  def get_todays_meta_file_name(self) -> str:
    return self.get_meta_log_file_name(datetime.today())
  
  def get_meta_log_file_name(self, date: datetime) -> str:
    date_str = date.strftime("%d-%m-%Y")
    return f"data/{self.folder_location}/{date_str}.meta"

  def write_metadata(self, data: FetchMetaData, overwrite: bool=True) -> str:
    file_name = self.get_todays_meta_file_name()
    if os.path.exists(file_name):
      if overwrite:
        os.remove(file_name)
      else:
        raise Exception("file already exists!")
    open(file_name, "w+").write(json.dumps(dataclasses.asdict(data), indent=4, sort_keys=True))

  def write(self, data: list[Manga], overwrite=True) -> str:
    file_name = self.get_todays_file_name()
    if os.path.exists(file_name):
      if overwrite:
        os.remove(file_name)
      else:
        raise Exception("file already exists!")
    with open(file_name, "w+") as file:
      file.writelines([str(d) + "\n" for d in data])
  
  def read_today(self) -> Optional[list[Manga]]:
    return self.read(datetime.today())

  def read(self, date: datetime) -> Optional[list[Manga]]:
    file_name = self.get_log_file_name(date)
    if not os.path.exists(file_name):
      return None
    file = open(file_name, "r")
    lines=  file.readlines()
    return [
      from_dict(data_class=Manga, data=json.loads(manga_data), config=Config(cast=[DiscountType]))
      for manga_data in lines
    ] 