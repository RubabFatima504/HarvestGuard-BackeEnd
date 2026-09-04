# """
# Database layer — SQLModel models + engine setup.

# DATABASE_URL should point at Postgres in any real deployment (see the
# DB-Auth-Deployment guide: Neon/Supabase give you this connection string for
# free). If DATABASE_URL isn't set, we fall back to a local SQLite file purely
# so the backend still runs out-of-the-box for local development without
# requiring a Postgres account first — do NOT rely on this fallback in
# production, since SQLite on most hosts doesn't survive a redeploy.
# """
# import os
# import json
# from datetime import datetime, timezone
# from typing import Optional

# from sqlmodel import SQLModel, Field, create_engine, Session

# DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./harvestguard_local.db")

# # Postgres connection strings from Neon/Supabase sometimes start with
# # "postgres://" (old Heroku-style scheme); SQLAlchemy needs "postgresql://".
# if DATABASE_URL.startswith("postgres://"):
#     DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
# engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)


# def _utcnow() -> datetime:
#     return datetime.now(timezone.utc)


# class User(SQLModel, table=True):
#     id: Optional[int] = Field(default=None, primary_key=True)
#     name: str
#     email: str = Field(unique=True, index=True)
#     password_hash: str
#     cooperative_name: Optional[str] = None
#     role: str = "Field Coordinator"
#     created_at: datetime = Field(default_factory=_utcnow)


# class Batch(SQLModel, table=True):
#     # batch_id stays a string like "MNG-A1B2C3" (not an autoincrement int) so
#     # existing frontend code that references batch ids doesn't need to change.
#     batch_id: str = Field(primary_key=True)
#     user_id: int = Field(foreign_key="user.id", index=True)

#     crop_id: str
#     quantity_kg: float
#     harvest_date: str
#     location_district: str
#     location_province: str = "Sindh"
#     latitude: float
#     longitude: float
#     storage_type: str = "open_air"
#     current_temp_celsius: Optional[float] = None
#     transport_available: bool = True
#     hours_to_nearest_market: float = 3.0
#     target_market_id: Optional[str] = None
#     farmer_name: Optional[str] = None
#     cooperative_name: Optional[str] = None

#     # The full assessment result (spoilage/market/advisory) is a nested,
#     # agent-shaped blob we never need to query into with SQL — storing it as
#     # a JSON text column is simpler and safer than modeling every nested
#     # field as its own table.
#     assessment_json: Optional[str] = None

#     created_at: datetime = Field(default_factory=_utcnow)

#     def assessment(self) -> Optional[dict]:
#         return json.loads(self.assessment_json) if self.assessment_json else None

#     def set_assessment(self, data: dict) -> None:
#         self.assessment_json = json.dumps(data)


# def init_db() -> None:
#     """Create tables on startup if they don't exist yet. Safe to call every boot."""
#     SQLModel.metadata.create_all(engine)


# def get_session():
#     """FastAPI dependency — yields a DB session per request."""
#     with Session(engine) as session:
#         yield session



"""
Database layer — SQLModel models + engine setup.

DATABASE_URL should point at Postgres in any real deployment (see the
DB-Auth-Deployment guide: Neon/Supabase give you this connection string for
free). If DATABASE_URL isn't set, we fall back to a local SQLite file purely
so the backend still runs out-of-the-box for local development without
requiring a Postgres account first — do NOT rely on this fallback in
production, since SQLite on most hosts doesn't survive a redeploy.
"""
import os
import json
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import SQLModel, Field, create_engine, Session

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./harvestguard_local.db")

# Postgres connection strings from Neon/Supabase sometimes start with
# "postgres://" (old Heroku-style scheme); SQLAlchemy needs "postgresql://".
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# pool_pre_ping: har request se pehle connection zinda hai ya nahi check
# karta hai (agar Neon/Supabase ne idle connection drop kar di ho, ek naya
# connection le leta hai instead of crashing with "SSL connection closed").
# pool_recycle: 5 min se purani connections ko proactively refresh karta hai.
# Dono sirf Postgres pe apply hote hain — SQLite ko inki zaroorat nahi.
pool_kwargs = {} if DATABASE_URL.startswith("sqlite") else {
    "pool_pre_ping": True,
    "pool_recycle": 300,
}
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args, **pool_kwargs)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str = Field(unique=True, index=True)
    password_hash: str
    cooperative_name: Optional[str] = None
    role: str = "Field Coordinator"
    created_at: datetime = Field(default_factory=_utcnow)


class Batch(SQLModel, table=True):
    # batch_id stays a string like "MNG-A1B2C3" (not an autoincrement int) so
    # existing frontend code that references batch ids doesn't need to change.
    batch_id: str = Field(primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)

    crop_id: str
    quantity_kg: float
    harvest_date: str
    location_district: str
    location_province: str = "Sindh"
    latitude: float
    longitude: float
    storage_type: str = "open_air"
    current_temp_celsius: Optional[float] = None
    transport_available: bool = True
    hours_to_nearest_market: float = 3.0
    target_market_id: Optional[str] = None
    farmer_name: Optional[str] = None
    cooperative_name: Optional[str] = None

    # The full assessment result (spoilage/market/advisory) is a nested,
    # agent-shaped blob we never need to query into with SQL — storing it as
    # a JSON text column is simpler and safer than modeling every nested
    # field as its own table.
    assessment_json: Optional[str] = None

    created_at: datetime = Field(default_factory=_utcnow)

    def assessment(self) -> Optional[dict]:
        return json.loads(self.assessment_json) if self.assessment_json else None

    def set_assessment(self, data: dict) -> None:
        self.assessment_json = json.dumps(data)


def init_db() -> None:
    """Create tables on startup if they don't exist yet. Safe to call every boot."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """FastAPI dependency — yields a DB session per request."""
    with Session(engine) as session:
        yield session

