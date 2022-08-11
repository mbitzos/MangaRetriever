from collections import defaultdict
from math import ceil
import threading
from tkinter.tix import MAX
from typing import Optional

from requests import HTTPError
from src.models import Discount, DiscountType, Manga, MangaCollection
from src.fetchers.fetcher import MangaFetcher
from src.util.multithread_processor import MultithreadProcessor

INDIGO_API_PAGE_SIZE_LIMIT = 12
ESTIMATED_MAX_MANGA = 25000
MAX_PAGES = ceil((ESTIMATED_MAX_MANGA * 1.0) / INDIGO_API_PAGE_SIZE_LIMIT)

class IndigoRetriever(MangaFetcher):
  MANGA_ID = 1200599
  URL = "https://www.chapters.indigo.ca/api/v1/search"
  DEFAULT_PARAMS = {
    'facetIds': MANGA_ID,
    'section': 2,
    'hybridPageId': MANGA_ID,
    'hybridPageName': 'manga',
    "searchKeys": "",
    "searchTerms": "",
    "sortKey": "",
    "sortDirection": "",
    "categoryIds": "",
    "pageSize": 100,
  }

  def is_eligible(self, data: dict) -> bool:
    if data['IsEbook']:
      return False
    return True

  def data_to_manga(self, data: dict) -> Optional[Manga]:
    discount = None
    adjusted_price = data['AdjustedPrice']
    list_price = data['ListPrice']
    if adjusted_price != list_price:
      type = DiscountType.PERCENTAGE
      discount_amount = data['SavingsPercentage']
      if data['HasDollarDiscount']:
        type = DiscountType.FLAT
        discount_amount = list_price-adjusted_price
      discount = Discount(
        type=type,
        old_price=list_price,
        discount_amount=discount_amount,
      )
    return Manga(
      id=data['Pid'],
      title=data['FullTitle'],
      publisher=data['Publisher'],
      is_oos=data['InStockQuantity'] == 0,
      is_preorder=data['IsPreorder'],
      is_coming_soon=data['IsComingSoon'],
      price=adjusted_price,
      discount=discount,
    )


  def _get_manga(self) -> MangaCollection:
    self._metadata.dynamic_data['failed_pages'] = []
    page_range = list(range(1, MAX_PAGES+1))
    self._metadata.dynamic_data['pages_processed'] = {i:0 for i in page_range}
    processor = MultithreadProcessor(page_range, self.get_manga_bulk, thread_count=100)
    mangas= MangaCollection(processor.run_and_aggregrate())

    # post processing stats
    pages_processed = self._metadata.dynamic_data['pages_processed'].items()
    self._metadata.dynamic_data['repeated_pages'] = [page for page,count in pages_processed if count > 1]
    failed_pages = self._metadata.dynamic_data['failed_pages']
    self._metadata.dynamic_data['missed_pages'] = list({page for page,count in pages_processed if count == 0} - set(failed_pages))

    # clean
    del self._metadata.dynamic_data['pages_processed']
    return mangas
  

  def get_manga_bulk(self, pages: list[int]) -> list[Manga]:
    mangas: list[Manga] = []
    for index, i in enumerate(pages):
      try:
        lock = threading.Lock()
        lock.acquire()
        self._metadata.dynamic_data['pages_processed'][i] += 1
        lock.release()
        mangas += self.get_single_request(i)

      except Exception as e: # no more pages
        self._metadata.dynamic_data['failed_pages'].append(i)
        self._metadata.dynamic_data['failed_pages'].extend(pages[index:])
        break
    return mangas

  def get_single_request(self, page: int) -> list[Manga]:
    params = {**self.DEFAULT_PARAMS, "pageNumber": page}
    data, _ = self.get_request(self.URL, params)
    products = data['Products']
    return [
      self.data_to_manga(product_data) for product_data in products
      if self.is_eligible(product_data)
    ]