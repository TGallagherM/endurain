"""FastAPI routes for the challenges feature."""

from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends, Security, status
from sqlalchemy.orm import Session

import activities.challenges.crud as challenges_crud
import activities.challenges.schema as challenges_schema
import auth.dependencies as auth_dependencies
import core.database as core_database
import users.users.dependencies as users_dependencies

router = APIRouter()


# @router.get(
#     "/",
#     response_model=list[challenges_schema.ChallengeRead],
#     status_code=status.HTTP_200_OK,
# )
@router.get(
    "",
    response_model=list[challenges_schema.ChallengeRead],
    status_code=status.HTTP_200_OK,
)
async def read_challenges(
    _check_scopes: Annotated[Callable, Security(auth_dependencies.check_scopes, scopes=["activities:read"])],
    token_user_id: Annotated[int, Depends(auth_dependencies.get_sub_from_access_token)],
    db: Annotated[Session, Depends(core_database.get_db)],
) -> list[challenges_schema.ChallengeRead]:
    """Return every challenge with membership totals and window mileage."""

    return challenges_crud.get_challenges_for_user(db, token_user_id)


@router.post(
    "",
    response_model=challenges_schema.ChallengeRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_challenge(
    payload: challenges_schema.ChallengeCreate,
    _check_scopes: Annotated[Callable, Security(auth_dependencies.check_scopes, scopes=["activities:read"])],
    token_user_id: Annotated[int, Depends(auth_dependencies.get_sub_from_access_token)],
    db: Annotated[Session, Depends(core_database.get_db)],
) -> challenges_schema.ChallengeRead:
    """Create a new fitness challenge for the authenticated user."""

    return challenges_crud.create_challenge(db, payload, token_user_id)


@router.delete(
    "/{challenge_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_challenge(
    challenge_id: int,
    _check_scopes: Annotated[Callable, Security(auth_dependencies.check_scopes, scopes=["activities:read"])],
    token_user_id: Annotated[int, Depends(auth_dependencies.get_sub_from_access_token)],
    db: Annotated[Session, Depends(core_database.get_db)],
) -> None:
    """Delete a challenge owned by the authenticated user."""

    challenges_crud.delete_challenge(db, challenge_id, token_user_id)


@router.get(
    "/{challenge_id}/members",
    response_model=list[challenges_schema.ChallengeMemberRead],
    status_code=status.HTTP_200_OK,
)
async def read_challenge_members(
    challenge_id: int,
    _check_scopes: Annotated[Callable, Security(auth_dependencies.check_scopes, scopes=["activities:read"])],
    _validate_challenge_id: Annotated[Callable, Depends(users_dependencies.validate_user_id)],
    db: Annotated[Session, Depends(core_database.get_db)],
) -> list[challenges_schema.ChallengeMemberRead]:
    """Return the participating members and their challenge-window mileage."""

    return challenges_crud.get_challenge_members(db, challenge_id)


@router.post(
    "/{challenge_id}/join",
    response_model=challenges_schema.ChallengeMembershipStatus,
    status_code=status.HTTP_201_CREATED,
)
async def join_challenge(
    challenge_id: int,
    _check_scopes: Annotated[Callable, Security(auth_dependencies.check_scopes, scopes=["activities:read"])],
    token_user_id: Annotated[int, Depends(auth_dependencies.get_sub_from_access_token)],
    db: Annotated[Session, Depends(core_database.get_db)],
) -> challenges_schema.ChallengeMembershipStatus:
    """Join the current user to a challenge."""

    return challenges_crud.join_challenge(db, challenge_id, token_user_id)


@router.delete(
    "/{challenge_id}/join",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def leave_challenge(
    challenge_id: int,
    _check_scopes: Annotated[Callable, Security(auth_dependencies.check_scopes, scopes=["activities:read"])],
    token_user_id: Annotated[int, Depends(auth_dependencies.get_sub_from_access_token)],
    db: Annotated[Session, Depends(core_database.get_db)],
) -> None:
    """Remove the current user from a challenge."""

    challenges_crud.leave_challenge(db, challenge_id, token_user_id)


@router.get(
    "/{challenge_id}/members/{user_id}/status",
    response_model=challenges_schema.ChallengeMembershipStatus,
    status_code=status.HTTP_200_OK,
)
async def read_membership_status(
    challenge_id: int,
    user_id: int,
    _check_scopes: Annotated[Callable, Security(auth_dependencies.check_scopes, scopes=["activities:read"])],
    db: Annotated[Session, Depends(core_database.get_db)],
) -> challenges_schema.ChallengeMembershipStatus:
    """Return how a user is currently participating in a challenge."""

    return challenges_crud.get_membership_status(db, challenge_id, user_id)
