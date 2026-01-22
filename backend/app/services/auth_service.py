from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import verify_password, hash_password

class AuthService:
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> User | None:
        """Authenticate user with email and password"""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user
    
    @staticmethod
    def create_user(db: Session, email: str, password: str, name: str = None) -> User:
        """Create new user"""
        hashed_password = hash_password(password)
        user = User(
            email=email,
            password_hash=hashed_password,
            name=name
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user