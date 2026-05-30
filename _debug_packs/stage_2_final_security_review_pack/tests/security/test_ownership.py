import pytest
from fastapi import HTTPException

from apps.api.app.security_foundation.ownership import assert_owner, is_owner


def test_is_owner_true():
    assert is_owner(1, 1) is True


def test_assert_owner_raises_for_non_owner():
    with pytest.raises(HTTPException):
        assert_owner(1, 2)
