from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AnimalEntry(BaseModel):
    id: Optional[int] = None
    image_hash: Optional[str] = None
    photo_url: Optional[str] = None
    number: str
    name: str
    scientific_name: Optional[str] = None
    category: Optional[str] = None
    height: Optional[str] = None
    weight: Optional[str] = None
    habitat: Optional[str] = None
    diet: Optional[str] = None
    predator: Optional[str] = None
    conservation: Optional[str] = None
    description: Optional[str] = None
    rarity: str = "普通"
    attributes: Optional[list[str]] = []
    scanned_at: Optional[datetime] = None


class IdentifyResponse(BaseModel):
    is_new: bool
    entry: AnimalEntry


class NoAnimalResponse(BaseModel):
    is_animal: bool = False
    message: str = "未发现动物，请对准动物重新扫描"


class CollectionResponse(BaseModel):
    total: int
    entries: list[dict]


class StatsResponse(BaseModel):
    total: int
    by_rarity: dict
    by_category: dict
    latest_scanned_at: Optional[str] = None
