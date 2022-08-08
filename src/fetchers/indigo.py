from math import ceil
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
    def get_manga_bulk_processor_method(page_range: list[int]) -> list[Manga]:
      return self.get_manga_bulk(page_range[0], page_range[-1])
    
    self._metadata.dynamic_data['failed_pages'] = []
    page_range = list(range(1, MAX_PAGES+1))
    processor = MultithreadProcessor(page_range, get_manga_bulk_processor_method, thread_count=100)
    return MangaCollection(processor.run_and_aggregrate())
  

  def get_manga_bulk(self, page_start: int, page_end: int) -> list[Manga]:
    mangas: list[Manga] = []
    for i in range(page_start, page_end+1):
      try:
        mangas += self.get_single_request(i)
      except Exception: # no more pages
        self._metadata.dynamic_data['failed_pages'].append(i)
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