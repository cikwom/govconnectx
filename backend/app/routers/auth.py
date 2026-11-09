from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.core.security import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models.location import LocalGovernmentArea, State
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, RoleUpdateRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


def validate_home_location(payload: RegisterRequest, db: Session) -> None:
    if bool(payload.home_state_code) != bool(payload.home_lga_code):
        raise HTTPException(status_code=400, detail="Select both your state and local government area")
    if payload.home_state_code:
        state = db.get(State, payload.home_state_code)
        lga = db.get(LocalGovernmentArea, payload.home_lga_code)
        if state is None or lga is None or lga.state_code != state.code:
            raise HTTPException(status_code=400, detail="The selected local government area does not belong to that state")


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists")
    validate_home_location(payload, db)
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role="citizen",
        home_state_code=payload.home_state_code,
        home_lga_code=payload.home_lga_code,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password", headers={"WWW-Authenticate": "Bearer"})
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account is disabled")
    return TokenResponse(access_token=create_access_token(user.id, user.role), user=user)


@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/users/{user_id}/role", response_model=UserResponse)
def update_user_role(user_id: int, payload: RoleUpdateRequest, db: Session = Depends(get_db), _: User = Depends(require_roles("system_admin"))):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.role = payload.role
    db.commit()
    db.refresh(user)
    return user
