"""retry_policy.py — Tenacity retry rules for World Bank API clients."""
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from src.core.exceptions import (
    WorldBankConnectionError,
    WorldBankHTTPStatusError,
    WorldBankTimeoutError,
)


def is_retryable_error(exc: BaseException) -> bool:
    """Determine if an exception should trigger a retry."""
    if isinstance(exc, (WorldBankTimeoutError, WorldBankConnectionError)):
        return True
    
    if isinstance(exc, WorldBankHTTPStatusError):
        msg = str(exc)
        if "status 5" in msg:
            return True
            
    return False


worldbank_retry_policy = retry(
    retry=retry_if_exception(is_retryable_error),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
