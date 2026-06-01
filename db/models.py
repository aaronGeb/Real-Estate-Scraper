"""'model"""

from datetime import datetime, UTC
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    Index,
    UniqueConstraint,
)

from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Property(Base):
    """core listing  one row per unique property"""

    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, autoincreament=True)
    external_id = Column(String(100), nullable=False)
    source = Column(String(20), nullable=Fasle)
    url = Column(Text, nullable=True)

    # Location

    address = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(50), nullable=False)
    zip_code = Column(String(20), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    neighborhood = Column(String(100), nullable=True)

    # property details
    property_type = Column(String(50), nullable=True)
    bedrooms = Column(Integer, nullable=True)
    bathrooms = Column(Integer, nullable=True)
    sqft = Column(Float, nullable=True)
    lot_size_sqft = Column(Float, nullable=True)
    year_built = Column(Integer, nullable=True)
    garage = Column(Boolean, nullable=True)
    pool = Column(Boolean, nullable=True)

    status = Column(String(30), nullable=True)
    days_on_market = Column(Integer, nullable=True)
    first_seen_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=True,
    )
    last_scraped_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    # Relationships
    price_history = relationship(
        "PriceHistory", back_populates="property", cascade="all, delete-orphan"
    )
    scrape_logs = relationship(
        "ScrapeLog", back_populates="property", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("external_id", "source", name="uq_property_source"),
        Index("ix_properties_city_state", "city", "state"),
        Index("ix_properties_status", "status"),
        Index("ix_properties_zip", "zip_code"),
    )

    def __repr__(self):
        return f"<Property {self.address}, {self.city} — {self.status}>"


class PriceHistory(Base):
    """One row per price observation — tracks changes over time."""

    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    property_id = Column(
        Integer,
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
    )
    price = Column(Float, nullable=False)
    price_per_sqft = Column(Float, nullable=True)
    event_type = Column(String(30), nullable=True)  # listed, reduced, sold
    recorded_at = Column(DateTime, default=datetime.utcnow)

    property = relationship("Property", back_populates="price_history")

    __table_args__ = (
        Index("ix_price_history_property_date", "property_id", "recorded_at"),
    )

    def __repr__(self):
        return f"<PriceHistory ${self.price:,.0f} on {self.recorded_at.date()}>"


class ScrapeLog(Base):
    """Audit log for every scrape run."""

    __tablename__ = "scrape_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    property_id = Column(
        Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=True
    )  # null = city-level log
    source = Column(String(20), nullable=False)
    city = Column(String(100), nullable=True)
    status = Column(String(20), nullable=False)  # success | error | skipped
    records_scraped = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    duration_secs = Column(Float, nullable=True)
    scraped_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    property = relationship("Property", back_populates="scrape_logs")

    __table_args__ = (
        Index("ix_scrape_logs_date", "scraped_at"),
        Index("ix_scrape_logs_source_status", "source", "status"),
    )
