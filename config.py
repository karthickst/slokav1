import os
from typing import Literal

class Config:
    """Configuration for production and test environments"""

    def __init__(self, mode: Literal["prod", "test"] = "test"):
        self.mode = mode
        self.is_production = mode == "prod"

        # Database configuration
        if self.is_production:
            self.database_url = os.getenv("POSTGRES_URL")
            if not self.database_url:
                raise ValueError("POSTGRES_URL environment variable is required in production mode")
        else:
            # Local test database
            self.database_url = os.getenv(
                "TEST_DATABASE_URL",
                "postgresql://localhost/course_management_test"
            )

        # JWT Secret
        self.jwt_secret = os.getenv("JWT_SECRET", "dev-secret-key-change-in-production")
        self.jwt_algorithm = "HS256"
        self.jwt_expiration_hours = 24

        # CORS settings
        if self.is_production:
            self.cors_origins = os.getenv("CORS_ORIGINS", "").split(",")
        else:
            self.cors_origins = ["*"]

        # Logging
        self.log_level = os.getenv("LOG_LEVEL", "DEBUG" if not self.is_production else "INFO")

        # App settings
        self.app_name = "Spiritual Course Management"
        self.app_version = "1.0.0"

    def __repr__(self):
        return f"<Config mode={self.mode} is_production={self.is_production}>"
