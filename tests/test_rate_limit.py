import pytest

from google_colab_mcp.security.rate_limit import RateLimiter
from google_colab_mcp.utils.errors import RateLimitError


def test_allows_requests_under_limit():
    limiter = RateLimiter(max_requests_per_minute=3)
    for _ in range(3):
        limiter.check("user-a")


def test_blocks_requests_over_limit():
    limiter = RateLimiter(max_requests_per_minute=2)
    limiter.check("user-b")
    limiter.check("user-b")
    with pytest.raises(RateLimitError):
        limiter.check("user-b")


def test_zero_disables_limiting():
    limiter = RateLimiter(max_requests_per_minute=0)
    for _ in range(100):
        limiter.check("user-c")


def test_per_principal_isolation():
    limiter = RateLimiter(max_requests_per_minute=1)
    limiter.check("user-d")
    limiter.check("user-e")  # different principal, own bucket
