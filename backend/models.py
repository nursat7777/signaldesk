"""Relational schema. Monetary columns are integer minor units, not SQLite REAL."""
from datetime import date, datetime, timezone
from sqlalchemy import BigInteger, Boolean, CheckConstraint, Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class Base(DeclarativeBase):
    pass

class ClientModel(Base):
    __tablename__ = 'clients'
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    currency: Mapped[str] = mapped_column(String(3))
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    campaigns: Mapped[list['CampaignModel']] = relationship(back_populates='client')
    __table_args__ = (CheckConstraint("currency IN ('KZT','USD','EUR')", name='ck_client_currency'),)

class UserModel(Base):
    __tablename__ = 'users'
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(16))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    client_id: Mapped[str | None] = mapped_column(ForeignKey('clients.id'))
    google_sub: Mapped[str | None] = mapped_column(String(255), unique=True)
    client: Mapped[ClientModel | None] = relationship()
    assignments: Mapped[list['AssignmentModel']] = relationship(back_populates='user', cascade='all, delete-orphan')
    sessions: Mapped[list['SessionModel']] = relationship(back_populates='user', cascade='all, delete-orphan')
    __table_args__ = (CheckConstraint("role IN ('admin','marketer','client')", name='ck_user_role'),
        CheckConstraint("(role='client' AND client_id IS NOT NULL) OR (role!='client' AND client_id IS NULL)", name='ck_user_client_role'))

class AssignmentModel(Base):
    __tablename__ = 'assignments'
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    client_id: Mapped[str] = mapped_column(ForeignKey('clients.id', ondelete='CASCADE'), primary_key=True)
    user: Mapped[UserModel] = relationship(back_populates='assignments')
    client: Mapped[ClientModel] = relationship()

class CampaignModel(Base):
    __tablename__ = 'campaigns'
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    client_id: Mapped[str] = mapped_column(ForeignKey('clients.id'), index=True)
    name: Mapped[str] = mapped_column(String(200))
    channel: Mapped[str] = mapped_column(String(32))
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    client: Mapped[ClientModel] = relationship(back_populates='campaigns')
    metrics: Mapped[list['MetricModel']] = relationship(back_populates='campaign')
    __table_args__ = (CheckConstraint("channel IN ('Google Ads','Meta Ads','TikTok Ads','Other')", name='ck_campaign_channel'),)

class MetricModel(Base):
    __tablename__ = 'daily_metrics'
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    campaign_id: Mapped[str] = mapped_column(ForeignKey('campaigns.id'), index=True)
    date: Mapped[date] = mapped_column(Date)
    spend_minor: Mapped[int] = mapped_column(BigInteger)
    revenue_minor: Mapped[int] = mapped_column(BigInteger)
    impressions: Mapped[int] = mapped_column(BigInteger)
    clicks: Mapped[int] = mapped_column(BigInteger)
    leads: Mapped[int] = mapped_column(BigInteger)
    sales: Mapped[int] = mapped_column(BigInteger)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)
    campaign: Mapped[CampaignModel] = relationship(back_populates='metrics')
    __table_args__ = (UniqueConstraint('campaign_id', 'date', name='uq_metric_campaign_date'),
        CheckConstraint('version >= 1', name='ck_metric_version'),
        CheckConstraint('spend_minor >= 0 AND revenue_minor >= 0', name='ck_metric_money'),
        CheckConstraint('impressions >= 0 AND clicks >= 0 AND leads >= 0 AND sales >= 0', name='ck_metric_counts'))

class SessionModel(Base):
    __tablename__ = 'sessions'
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    csrf: Mapped[str] = mapped_column(String(64))
    expires: Mapped[float] = mapped_column(Float, index=True)
    user: Mapped[UserModel] = relationship(back_populates='sessions')

class OAuthTransactionModel(Base):
    __tablename__ = 'oauth_transactions'
    state_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    nonce: Mapped[str] = mapped_column(String(64))
    expires: Mapped[float] = mapped_column(Float, index=True)
