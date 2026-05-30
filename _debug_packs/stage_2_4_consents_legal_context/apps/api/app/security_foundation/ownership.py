from __future__ import annotations

from fastapi import HTTPException, status


def assert_owner(resource_user_id: int | str, current_user_id: int | str) -> None:
    if str(resource_user_id) != str(current_user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Resource not found',
        )


def is_owner(resource_user_id: int | str, current_user_id: int | str) -> bool:
    return str(resource_user_id) == str(current_user_id)
