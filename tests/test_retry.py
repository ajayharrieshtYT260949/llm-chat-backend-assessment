
from unittest.mock import Mock

import pytest
from tenacity import RetryError

from app.llm.retry import (
    is_retryable_error,
    retry_llm_request,
)


class FakeHTTPError(Exception):
    def __init__(self, status_code):
        self.status_code = status_code
        super().__init__(f"HTTP {status_code}")


def test_429_retries_then_succeeds():
    mock_request = Mock(
        side_effect=[
            FakeHTTPError(429),
            FakeHTTPError(429),
            "Success",
        ]
    )

    decorated_request = retry_llm_request(mock_request)  
    result = decorated_request()

    assert result == "Success"
    assert mock_request.call_count == 3


def test_401_does_not_retry():
    mock_request = Mock(
        side_effect=FakeHTTPError(401)
    )

    decorated_request = retry_llm_request(mock_request)

    with pytest.raises(FakeHTTPError):
        decorated_request()

    assert mock_request.call_count == 1


def test_500_retries_then_succeeds():
    mock_request = Mock(
        side_effect=[
            FakeHTTPError(500),
            "Success",
        ]
    )

    decorated_request = retry_llm_request(mock_request) 

    result = decorated_request()

    assert result == "Success"
    assert mock_request.call_count == 2


def test_503_stops_after_five_attempts():
    mock_request = Mock(
        side_effect=FakeHTTPError(503)
    )

    decorated_request = retry_llm_request(mock_request)
    with pytest.raises(FakeHTTPError):
        decorated_request()

    assert mock_request.call_count == 5


@pytest.mark.parametrize(
    "status_code, expected",
    [
        (429, True),
        (500, True),
        (502, True),
        (503, True),
        (599, True),
        (400, False),
        (401, False),
        (403, False),
    ],
)
def test_retryable_error_status_codes(status_code, expected):
    error = FakeHTTPError(status_code)

    assert is_retryable_error(error) is expected
