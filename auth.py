import logging
import traceback
from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
from passlib.context import CryptContext
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthManager:
    """Authentication and authorization management"""

    def __init__(self, config: Config):
        self.config = config
        logger.info(f"Initializing AuthManager with config: {config}")

    def hash_password(self, password: str) -> str:
        """Hash a password"""
        try:
            logger.debug("Hashing password")
            hashed = pwd_context.hash(password)
            logger.debug("Password hashed successfully")
            return hashed
        except Exception as e:
            logger.error(f"Password hashing failed: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        try:
            logger.debug("Verifying password")
            result = pwd_context.verify(plain_password, hashed_password)
            logger.debug(f"Password verification result: {result}")
            return result
        except Exception as e:
            logger.error(f"Password verification failed: {str(e)}")
            logger.error(traceback.format_exc())
            return False

    def create_access_token(self, data: Dict, user_type: str = "student") -> str:
        """
        Create a JWT access token

        Args:
            data: User data to encode (should include 'sub' with user identifier)
            user_type: Type of user ('student' or 'admin')
        """
        try:
            logger.info(f"Creating access token for {user_type}: {data.get('sub')}")

            to_encode = data.copy()
            expire = datetime.utcnow() + timedelta(hours=self.config.jwt_expiration_hours)

            to_encode.update({
                "exp": expire,
                "type": user_type,
                "iat": datetime.utcnow()
            })

            encoded_jwt = jwt.encode(
                to_encode,
                self.config.jwt_secret,
                algorithm=self.config.jwt_algorithm
            )

            logger.info(f"Access token created successfully, expires at {expire}")
            return encoded_jwt

        except Exception as e:
            logger.error(f"Token creation failed: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    def verify_token(self, token: str) -> Optional[Dict]:
        """
        Verify and decode a JWT token

        Returns:
            Decoded token payload if valid, None otherwise
        """
        try:
            logger.debug("Verifying token")

            payload = jwt.decode(
                token,
                self.config.jwt_secret,
                algorithms=[self.config.jwt_algorithm]
            )

            logger.debug(f"Token verified successfully for user: {payload.get('sub')}")
            return payload

        except JWTError as e:
            logger.warning(f"Token verification failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            logger.error(traceback.format_exc())
            return None

    def validate_email(self, email: str) -> bool:
        """Basic email validation"""
        try:
            logger.debug(f"Validating email: {email}")

            if not email or "@" not in email or "." not in email:
                logger.warning(f"Invalid email format: {email}")
                return False

            logger.debug("Email validation passed")
            return True

        except Exception as e:
            logger.error(f"Email validation error: {str(e)}")
            logger.error(traceback.format_exc())
            return False

    def validate_password(self, password: str) -> tuple[bool, str]:
        """
        Validate password strength

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            logger.debug("Validating password strength")

            if not password:
                return False, "Password is required"

            if len(password) < 6:
                return False, "Password must be at least 6 characters long"

            logger.debug("Password validation passed")
            return True, ""

        except Exception as e:
            logger.error(f"Password validation error: {str(e)}")
            logger.error(traceback.format_exc())
            return False, "Password validation failed"


def get_auth_manager(config: Config) -> AuthManager:
    """Factory function to get AuthManager instance"""
    return AuthManager(config)
