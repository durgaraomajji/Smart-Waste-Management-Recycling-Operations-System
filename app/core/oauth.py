"""Google OAuth2 / OpenID Connect client (Authlib). Only registered when credentials are configured."""
from authlib.integrations.starlette_client import OAuth

from app.core.config import settings

oauth = OAuth()

if settings.google_enabled:
    oauth.register(
        name="google",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )
