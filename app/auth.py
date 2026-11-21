
import secrets

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.dependencies import get_app_settings


api_key_header = APIKeyHeader(
    name="x-api-key",
    auto_error=False,
)


def verify_api_key(
    api_key: str | None = Security(api_key_header),
    settings=Depends(get_app_settings),
) -> str:
    """
    Validate the API key supplied in the x-api-key header.

    Missing key: 401 Unauthorized
    Invalid key: 403 Forbidden
    Valid key: return the supplied key.
    """

    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required.",
        )

    if not secrets.compare_digest(
        api_key,
        settings.chat_api_key,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key.",
        )

    return api_key
