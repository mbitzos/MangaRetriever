import dataclasses
import enum
from typing import Optional

from src.util.utils import JSONSerializableDataclass


class DiscountType(str, enum.Enum):
  PERCENTAGE = "Percentage"
  FLAT = "Flat"

@dataclasses.dataclass
class Discount:
  type: DiscountType
  discount_amount: float
  old_price: float
  
@dataclasses.dataclass
class Manga(JSONSerializableDataclass):
  id: str
  title: str
  publisher: str
  is_oos: bool
  is_preorder: bool
  is_coming_soon: bool
  price: float
  discount: Optional[Discount] = None

  def get_discount_diff(self) -> Optional[float]:
    if not self.discount:
      return None
    else:
      return self.discount.old_price - self.price

class MangaCollection(list[Manga]):
  def get_discounted(self) -> list[Manga]:
    return sorted([m for m in self if m.discount], key=lambda m: m.get_discount_diff())
