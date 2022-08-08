import datetime
from datetime import datetime
from dacite import Config, from_dict
import json

import os
from typing import Optional
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