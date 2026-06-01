"""CRUD"""

from datetime import datetime, UTC
from typing import Optional
from sqlalchemy.orm import Session, select, func
from loguru import logger
from db.models import Property, PriceHistory, ScrapeLog


def upsert_property(session: Session, data: dict) -> tuple[Property, bool]:
    """
    Insert a new property or update an existing one.
    Returns
    (property, created) where created=True means a new row was inserted.
    """
    prop = (
        session.query(Property)
        .filter_by(external_id=data["external_id"], source=data["source"])
        .first()
    )
    created = prop is None
    if created:
        prop = property(**{k: v for k, v in data.items() if k != "price"})
        session.add(prop)
        session.flush()
        logger.debug(f"new property: {prop.address}")
    else:
        for key, value in data.items():
            if key != "price" and hasattr(prop, key):
                setattr(prop, key, value)
        prop.last_scraped_at = datetime.now(UTC)
    return prop, created


def get_properties(
    session: Session,
    city: Optional[str] = None,
    state: Optional[str] = None,
    status: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_beds: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Property]:
    q = session.query(Property)
    if city:
        q = q.filter(Property.city.ilike(f"%{city}%"))
    if state:
        q = q.filter(Property.state.ilike(f"%{state}%"))
    if status:
        q = q.filter(Property.status == status)
    if min_beds:
        q = q.filter(Property.bedrooms >= min_beds)

    if min_price or max_price:

        latest_price_sub = (
            select(
                PriceHistory.property_id,
                func.max(PriceHistory.recorded_at).label("latest_date"),
            )
            .group_by(PriceHistory.property_id)
            .subquery()
        )
        latest_price = (
            select(PriceHistory.property_id, PriceHistory.price)
            .join(
                latest_price_sub,
                (PriceHistory.property_id == latest_price_sub.c.property_id)
                & (PriceHistory.recorded_at == latest_price_sub.c.latest_date),
            )
            .subquery()
        )
        q = q.join(latest_price, Property.id == latest_price.c.property_id)
        if min_price:
            q = q.filter(latest_price.c.price >= min_price)
        if max_price:
            q = q.filter(latest_price.c.price <= max_price)

    return q.order_by(Property.last_scraped_at.desc()).limit(limit).offset(offset).all()


def record_price(
    session: Session,
    property_id: int,
    price: float,
    event_type: str = "listed",
    sqft: Optional[int] = None,
) -> PriceHistory:
    price_per_sqft = round(price / sqft, 2) if sqft and sqft > 0 else None
    entry = PriceHistory(
        property_id=property_id,
        price=price,
        price_per_sqft=price_per_sqft,
        event_type=event_type,
    )
    session.add(entry)
    return entry


def get_price_history(session: Session, property_id: int) -> list[PriceHistory]:
    return (
        session.query(PriceHistory)
        .filter_by(property_id=property_id)
        .order_by(PriceHistory.recorded_at.asc())
        .all()
    )


def log_scrape(
    session: Session,
    source: str,
    city: str,
    status: str,
    records_scraped: int = 0,
    error_message: Optional[str] = None,
    duration_secs: Optional[float] = None,
    property_id: Optional[int] = None,
) -> ScrapeLog:
    entry = ScrapeLog(
        source=source,
        city=city,
        status=status,
        records_scraped=records_scraped,
        error_message=error_message,
        duration_secs=duration_secs,
        property_id=property_id,
    )
    session.add(entry)
    return entry


def get_scrape_stats(session: Session) -> dict:
    total = session.query(func.count(ScrapeLog.id)).scalar()
    success = (
        session.query(func.count(ScrapeLog.id)).filter_by(status="success").scalar()
    )
    errors = session.query(func.count(ScrapeLog.id)).filter_by(status="error").scalar()
    total_records = session.query(func.sum(ScrapeLog.records_scraped)).scalar() or 0
    return {
        "total_runs": total,
        "successful_runs": success,
        "failed_runs": errors,
        "total_records_scraped": total_records,
    }
