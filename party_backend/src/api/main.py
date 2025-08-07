from fastapi import FastAPI, Depends, HTTPException, Path
from fastapi import APIRouter
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from . import models
from . import schemas
from .deps import get_db, hash_password, verify_password, create_access_token, get_current_user
from fastapi.security import OAuth2PasswordRequestForm

app = FastAPI(
    title="Party Planner API",
    description="API for user authentication, events, guests, invitations, and RSVPs.",
    version="1.0.0",
    openapi_tags=[
        {"name": "auth", "description": "Authentication"},
        {"name": "events", "description": "Event management"},
        {"name": "guests", "description": "Guest/invitation management"},
        {"name": "rsvps", "description": "RSVP management"}
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["health"])
def health_check():
    """
    Health check endpoint.
    Returns a simple healthy message.
    """
    return {"message": "Healthy"}

# ========== AUTH ROUTES ==========

auth_router = APIRouter(prefix="/auth", tags=["auth"])

# PUBLIC_INTERFACE
@auth_router.post("/signup", response_model=schemas.UserOut, summary="Sign up user")
def signup(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    existing = db.query(models.User).filter(
        (models.User.username == user_data.username) | (models.User.email == user_data.email)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username or Email already exists.")
    hashed = hash_password(user_data.password)
    user = models.User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# PUBLIC_INTERFACE
@auth_router.post("/login", response_model=schemas.Token, summary="Login user")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Authenticate a user and return a JWT token.
    """
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token = create_access_token({"sub": user.id})
    return schemas.Token(access_token=token, token_type="bearer")


# ========== EVENT ROUTES ==========

event_router = APIRouter(prefix="/events", tags=["events"])

# PUBLIC_INTERFACE
@event_router.post("/", response_model=schemas.EventOut, summary="Create event")
def create_event(
    event_data: schemas.EventCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)):
    """Create a new event for current user."""
    event = models.Event(**event_data.dict(), owner_id=user.id)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

# PUBLIC_INTERFACE
@event_router.get("/", response_model=List[schemas.EventOut], summary="List all events")
def list_events(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50,
    user: models.User = Depends(get_current_user),
):
    """List all events for the current user."""
    return db.query(models.Event).filter(models.Event.owner_id == user.id).offset(skip).limit(limit).all()

# PUBLIC_INTERFACE
@event_router.get("/{event_id}", response_model=schemas.EventOut, summary="Get event details")
def get_event(
    event_id: int = Path(..., description="ID of the event"),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Get a specific event."""
    event = db.query(models.Event).filter(models.Event.id == event_id, models.Event.owner_id == user.id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

# PUBLIC_INTERFACE
@event_router.put("/{event_id}", response_model=schemas.EventOut, summary="Update event")
def update_event(
    event_id: int,
    event_update: schemas.EventUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    """Update an event. Only owner can update."""
    event = db.query(models.Event).filter(models.Event.id == event_id, models.Event.owner_id == user.id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    for field, value in event_update.dict(exclude_unset=True).items():
        setattr(event, field, value)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

# PUBLIC_INTERFACE
@event_router.delete("/{event_id}", response_model=dict, summary="Delete event")
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    """Delete an event."""
    event = db.query(models.Event).filter(models.Event.id == event_id, models.Event.owner_id == user.id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    db.delete(event)
    db.commit()
    return {"detail": "Event deleted"}


# ========== GUEST/INVITE ROUTES ==========

guest_router = APIRouter(prefix="/events/{event_id}/guests", tags=["guests"])

# PUBLIC_INTERFACE
@guest_router.post("/", response_model=schemas.GuestOut, summary="Add guest to event")
def add_guest(
    event_id: int,
    guest: schemas.GuestCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    """Add a guest to an event (must be owner)."""
    event = db.query(models.Event).filter(models.Event.id == event_id, models.Event.owner_id == user.id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    new_guest = models.Guest(
        event_id=event.id,
        name=guest.name,
        email=guest.email,
        invited_by_user_id=user.id,
        responded=False
    )
    db.add(new_guest)
    db.commit()
    db.refresh(new_guest)
    return new_guest

# PUBLIC_INTERFACE
@guest_router.get("/", response_model=List[schemas.GuestOut], summary="List event guests")
def list_guests(
    event_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    """List all guests for an event (owner only)."""
    event = db.query(models.Event).filter(models.Event.id == event_id, models.Event.owner_id == user.id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return db.query(models.Guest).filter(models.Guest.event_id == event_id).all()


# ========== INVITE (BATCH) ROUTES ==========

invite_router = APIRouter(prefix="/events/{event_id}/invite", tags=["guests"])

# PUBLIC_INTERFACE
@invite_router.post("/", response_model=List[schemas.GuestOut], summary="Invite (batch add) guests by email")
def invite_guests(
    event_id: int,
    invite_request: schemas.InviteRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    """Batch invite guests to an event (owner only, by email)."""
    event = db.query(models.Event).filter(models.Event.id == event_id, models.Event.owner_id == user.id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    guests = []
    for email in invite_request.guest_emails:
        guest = db.query(models.Guest).filter(models.Guest.event_id == event_id, models.Guest.email == email).first()
        if not guest:
            new_guest = models.Guest(
                event_id=event_id,
                name=email.split('@')[0],  # Default to prefix of email for name
                email=email,
                invited_by_user_id=user.id,
                responded=False
            )
            db.add(new_guest)
            guests.append(new_guest)
    db.commit()
    # Refresh all returned
    for g in guests:
        db.refresh(g)
    return guests

# ========== RSVP ROUTES ==========

rsvp_router = APIRouter(prefix="/events/{event_id}/rsvp", tags=["rsvps"])

# PUBLIC_INTERFACE
@rsvp_router.post("/", response_model=schemas.RSVPOut, summary="RSVP to event")
def rsvp_to_event(
    event_id: int,
    rsvp: schemas.RSVPCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    """
    RSVP to an event (by guest/user). Will create or update an RSVP record.
    """
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Only RSVP to events user is a guest of, or owner
    guest = db.query(models.Guest).filter(models.Guest.event_id == event_id, models.Guest.email == user.email).first()
    if not guest and event.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Must be invited or owner")

    # Check if RSVP exists
    rsvp_obj = db.query(models.RSVP).filter(models.RSVP.event_id == event_id, models.RSVP.user_id == user.id).first()
    if not rsvp_obj:
        rsvp_obj = models.RSVP(
            event_id=event_id,
            user_id=user.id,
            status=rsvp.status
        )
        db.add(rsvp_obj)
        db.commit()
        db.refresh(rsvp_obj)
    else:
        rsvp_obj.status = rsvp.status
        db.commit()
        db.refresh(rsvp_obj)
    return rsvp_obj

# PUBLIC_INTERFACE
@rsvp_router.get("/", response_model=schemas.RSVPOut, summary="Get user's RSVP status")
def get_my_rsvp_status(
    event_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    """Get the current user's RSVP status for an event."""
    rsvp = db.query(models.RSVP).filter(
        models.RSVP.event_id == event_id,
        models.RSVP.user_id == user.id
    ).first()
    if not rsvp:
        raise HTTPException(status_code=404, detail="RSVP not found")
    return rsvp

# Route registration
app.include_router(auth_router)
app.include_router(event_router)
app.include_router(guest_router)
app.include_router(invite_router)
app.include_router(rsvp_router)
