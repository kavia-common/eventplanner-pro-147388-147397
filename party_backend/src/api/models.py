from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from .database import Base

# PUBLIC_INTERFACE
class User(Base):
    """Party Planner user model."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(128), unique=True, nullable=False, index=True)
    hashed_password = Column(String(256), nullable=False)

    events = relationship("Event", back_populates="owner")
    rsvps = relationship("RSVP", back_populates="user")


# PUBLIC_INTERFACE
class Event(Base):
    """Event details and owner."""
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(128), nullable=False)
    description = Column(Text)
    date = Column(DateTime, nullable=False)
    location = Column(String(256), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="events")
    guests = relationship("Guest", back_populates="event", cascade="all, delete-orphan")
    rsvps = relationship("RSVP", back_populates="event", cascade="all, delete-orphan")


# PUBLIC_INTERFACE
class Guest(Base):
    """Guests invited to events."""
    __tablename__ = "guests"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    name = Column(String(128), nullable=False)
    email = Column(String(128), nullable=False)
    invited_by_user_id = Column(Integer, ForeignKey("users.id"))
    responded = Column(Boolean, default=False)

    event = relationship("Event", back_populates="guests")


# PUBLIC_INTERFACE
class RSVP(Base):
    """Tracks RSVP status for users and events."""
    __tablename__ = "rsvps"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String(16), nullable=False)  # e.g. 'accepted', 'declined', 'maybe'

    event = relationship("Event", back_populates="rsvps")
    user = relationship("User", back_populates="rsvps")
