
import logging

from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_random_exponential,
)

logger = logging.getLogger(__name__)


def is_retryable_error(exception: BaseException) -> bool:
    """
    Retry only HTTP 429 and HTTP 5xx errors.
    """

    status_code = getattr(exception, "status_code", None)

    return (
        status_code == 429
        or (
            isinstance(status_code, int)
            and 500 <= status_code <= 599
        )
    )


def log_retry_attempt(retry_state) -> None:
    """
    Log the retry attempt and the next waiting time.
    """

    exception = retry_state.outcome.exception()
    wait_time = retry_state.next_action.sleep

    logger.warning(
        "Retry attempt %s after error: %s. "
        "Waiting %.2f seconds before retrying.",
        retry_state.attempt_number,
        exception,
        wait_time,
    )


retry_llm_request = retry(
    retry=retry_if_exception(is_retryable_error),
    wait=wait_random_exponential(
        multiplier=1,
        min=1,
        max=16,
    ),
    stop=stop_after_attempt(5),
    before_sleep=log_retry_attempt,
    reraise=True,
)
