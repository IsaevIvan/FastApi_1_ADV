from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

from app.database import get_db, Advertisement, create_tables


# Модели Pydantic
class AdvertisementCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    price: float = Field(..., gt=0)
    author: str = Field(..., min_length=1, max_length=50)


class AdvertisementResponse(BaseModel):
    id: int
    title: str
    description: str
    price: float
    author: str
    created_at: datetime

    class Config:
        from_attributes = True


class AdvertisementUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    price: Optional[float] = Field(None, gt=0)
    author: Optional[str] = Field(None, min_length=1, max_length=50)


# Создаем приложение
app = FastAPI(title="Advertisement Service", version="1.0.0")


# Создаем таблицы при запуске
@app.on_event("startup")
def startup():
    create_tables()


# CRUD endpoints
@app.post("/advertisement", response_model=AdvertisementResponse, status_code=201)
def create_advertisement(ad: AdvertisementCreate, db: Session = Depends(get_db)):
    db_ad = Advertisement(**ad.model_dump())
    db.add(db_ad)
    db.commit()
    db.refresh(db_ad)
    return db_ad


@app.get("/advertisement/{ad_id}", response_model=AdvertisementResponse)
def get_advertisement(ad_id: int, db: Session = Depends(get_db)):
    ad = db.query(Advertisement).filter(Advertisement.id == ad_id).first()
    if not ad:
        raise HTTPException(status_code=404, detail="Advertisement not found")
    return ad


@app.patch("/advertisement/{ad_id}", response_model=AdvertisementResponse)
def update_advertisement(ad_id: int, ad_data: AdvertisementUpdate, db: Session = Depends(get_db)):
    ad = db.query(Advertisement).filter(Advertisement.id == ad_id).first()
    if not ad:
        raise HTTPException(status_code=404, detail="Advertisement not found")

    update_data = ad_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(ad, key, value)

    db.commit()
    db.refresh(ad)
    return ad


@app.delete("/advertisement/{ad_id}", status_code=204)
def delete_advertisement(ad_id: int, db: Session = Depends(get_db)):
    ad = db.query(Advertisement).filter(Advertisement.id == ad_id).first()
    if not ad:
        raise HTTPException(status_code=404, detail="Advertisement not found")

    db.delete(ad)
    db.commit()
    return


@app.get("/advertisement", response_model=List[AdvertisementResponse])
def search_advertisements(
        title: Optional[str] = None,
        author: Optional[str] = None,
        min_price: Optional[float] = Query(None, gt=0),
        max_price: Optional[float] = Query(None, gt=0),
        db: Session = Depends(get_db)
):
    query = db.query(Advertisement)

    if title:
        query = query.filter(Advertisement.title.ilike(f"%{title}%"))
    if author:
        query = query.filter(Advertisement.author.ilike(f"%{author}%"))
    if min_price:
        query = query.filter(Advertisement.price >= min_price)
    if max_price:
        query = query.filter(Advertisement.price <= max_price)

    return query.order_by(Advertisement.created_at.desc()).all()


@app.get("/")
def root():
    return {"message": "Advertisement Service API"}