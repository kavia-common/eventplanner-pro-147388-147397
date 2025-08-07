from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field

# User Schemas
# PUBLIC_INTERFACE
class UserBase(BaseModel):
    username: str = Field(..., description="Unique username of the user")
    email: EmailStr = Field(..., description="User email address")

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="User password")  # Write only during creation

class UserOut(UserBase):
    id: int

    class Config:
        orm_mode = True

# PUBLIC_INTERFACE
class UserLogin(BaseModel):
    username: str
    password: str

# Authentication Response Schema
# PUBLIC_INTERFACE
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# Event Schemas
# PUBLIC_INTERFACE
class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    date: datetime
    location: str

class EventCreate(EventBase):
    pass

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[datetime] = None
    location: Optional[str] = None

class EventOut(EventBase):
    id: int
    owner_id: int

    class Config:
        orm_mode = True

# PUBLIC_INTERFACE
class GuestBase(BaseModel):
    name: str
    email: EmailStr

class GuestCreate(GuestBase):
    pass

class GuestOut(GuestBase):
    id: int
    event_id: int

    class Config:
        orm_mode = True

# PUBLIC_INTERFACE
class RSVPBase(BaseModel):
    status: str = Field(..., description="RSVP status: accepted, declined, maybe")

class RSVPCreate(RSVPBase):
    pass

class RSVPOut(RSVPBase):
    id: int
    event_id: int
    user_id: int

    class Config:
        orm_mode = True

# PUBLIC_INTERFACE
class InviteRequest(BaseModel):
    guest_emails: List[EmailStr] = Field(..., description="List of emails to invite")
