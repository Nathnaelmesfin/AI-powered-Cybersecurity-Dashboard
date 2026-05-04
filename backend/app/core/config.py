import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+pysqlite:///./sentinelops.db")
API_TOKEN = os.getenv("SENTINELOPS_API_TOKEN", "change-me")
JWT_SECRET = os.getenv("SENTINELOPS_JWT_SECRET", "dev-secret-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("SENTINELOPS_JWT_EXPIRE_MINUTES", "120"))
AUTH_MODE = os.getenv("SENTINELOPS_AUTH_MODE", "local")  # local|oidc
OIDC_ISSUER = os.getenv("SENTINELOPS_OIDC_ISSUER", "")
OIDC_AUDIENCE = os.getenv("SENTINELOPS_OIDC_AUDIENCE", "sentinelops-api")
OIDC_JWKS_URL = os.getenv("SENTINELOPS_OIDC_JWKS_URL", "")
