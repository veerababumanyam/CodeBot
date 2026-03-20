"""Authentication service handling user registration, login, and API keys."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from codebot.auth.api_key import generate_api_key
from codebot.auth.password import hash_password, verify_password
from codebot.db.models.user import ApiKey, User, UserRole


class AuthService:
    """Business logic for authentication operations.

    Args:
        db: Async database session.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def register(
        self,
        email: str,
        password: str,
        name: str,
        organization: str | None = None,
    ) -> User:
        """Register a new user.

        Args:
            email: User's email address (must be unique).
            password: Plaintext password (will be hashed).
            name: Display name.
            organization: Optional organization name.

        Returns:
            The created User ORM object.

        Raises:
            HTTPException: 409 if the email is already registered.
        """
        result = await self._db.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        user = User(
            email=email,
            password_hash=hash_password(password),
            name=name,
            role=UserRole.USER,
            organization=organization,
        )
        self._db.add(user)
        await self._db.commit()
        await self._db.refresh(user)
        return user

    async def login(self, email: str, password: str) -> User:
        """Authenticate a user with email and password.

        Args:
            email: User's email address.
            password: Plaintext password to verify.

        Returns:
            The authenticated User ORM object.

        Raises:
            HTTPException: 401 if credentials are invalid.
        """
        result = await self._db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is None or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        user.last_login_at = datetime.now(UTC)
        await self._db.commit()
        await self._db.refresh(user)
        return user

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        """Look up a user by ID.

        Args:
            user_id: The user's UUID.

        Returns:
            The User if found, else None.
        """
        return await self._db.get(User, user_id)

    async def create_api_key(self, user_id: UUID, name: str) -> tuple[ApiKey, str]:
        """Create a new API key for a user.

        Args:
            user_id: The owning user's UUID.
            name: Human-readable label for the key.

        Returns:
            Tuple of (ApiKey ORM object, raw_key string).
        """
        raw_key, key_hash, prefix = generate_api_key()
        api_key_obj = ApiKey(
            user_id=user_id,
            name=name,
            key_hash=key_hash,
            key_prefix=prefix,
        )
        self._db.add(api_key_obj)
        await self._db.commit()
        await self._db.refresh(api_key_obj)
        return api_key_obj, raw_key

    async def list_api_keys(self, user_id: UUID) -> list[ApiKey]:
        """List all API keys for a user.

        Args:
            user_id: The owning user's UUID.

        Returns:
            List of ApiKey ORM objects.
        """
        result = await self._db.execute(select(ApiKey).where(ApiKey.user_id == user_id))
        return list(result.scalars().all())
