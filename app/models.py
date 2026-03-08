from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    comments: Mapped[list['Comment']] = relationship(back_populates='user', cascade='all,delete')
    photos: Mapped[list['Photo']] = relationship(back_populates='user', cascade='all,delete')


class GuardrailFeature(Base):
    __tablename__ = 'guardrail_features'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    feature_type: Mapped[str] = mapped_column(String(64), default='guardrail_terminal')
    is_broken: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[str] = mapped_column(String(64), default='osm')
    source_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    comments: Mapped[list['Comment']] = relationship(back_populates='feature', cascade='all,delete')
    photos: Mapped[list['Photo']] = relationship(back_populates='feature', cascade='all,delete')


class Comment(Base):
    __tablename__ = 'comments'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    feature_id: Mapped[int] = mapped_column(ForeignKey('guardrail_features.id'), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    feature: Mapped['GuardrailFeature'] = relationship(back_populates='comments')
    user: Mapped['User'] = relationship(back_populates='comments')


class Photo(Base):
    __tablename__ = 'photos'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    feature_id: Mapped[int] = mapped_column(ForeignKey('guardrail_features.id'), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    object_key: Mapped[str] = mapped_column(String(512), nullable=False)
    image_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    feature: Mapped['GuardrailFeature'] = relationship(back_populates='photos')
    user: Mapped['User'] = relationship(back_populates='photos')
