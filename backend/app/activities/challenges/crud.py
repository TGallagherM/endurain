"""CRUD operations for fitness challenges."""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import and_, delete, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

import activities.activity.models as activity_models
import activities.challenges.models as challenges_models
import activities.challenges.schema as challenges_schema
import core.logger as core_logger
import followers.models as followers_models
import users.users.models as users_models


def _internal_server_error(err: Exception, context: str) -> HTTPException:
    """Build a logged HTTP 500 error from a database exception."""

    core_logger.print_to_log(f"Error in {context}: {err}", "error", exc=err)
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal Server Error",
    )


def get_challenges_for_user(db: Session, user_id: int) -> list[challenges_schema.ChallengeRead]:
    """Return every challenge with challenge-window mileage and membership counts."""

    try:
        challenges = db.execute(select(challenges_models.Challenge).order_by(challenges_models.Challenge.start_date)).scalars().all()
        result: list[challenges_schema.ChallengeRead] = []
        for challenge in challenges:
            member_count = db.execute(
                select(func.count(challenges_models.ChallengeMember.user_id)).where(
                    challenges_models.ChallengeMember.challenge_id == challenge.id,
                ),
            ).scalar_one() or 0
            total_distance_meters = db.execute(
                select(func.coalesce(func.sum(activity_models.Activity.distance), 0)).where(
                    activity_models.Activity.user_id.in_(
                        select(challenges_models.ChallengeMember.user_id).where(
                            challenges_models.ChallengeMember.challenge_id == challenge.id,
                        ),
                    ),
                    activity_models.Activity.start_time >= datetime.combine(challenge.start_date, datetime.min.time(), tzinfo=UTC),
                    activity_models.Activity.start_time < datetime.combine(challenge.end_date, datetime.min.time(), tzinfo=UTC),
                ),
            ).scalar_one() or 0
            result.append(
                challenges_schema.ChallengeRead(
                    id=challenge.id,
                    name=challenge.name,
                    start_date=challenge.start_date,
                    end_date=challenge.end_date,
                    created_by_user_id=challenge.created_by_user_id,
                    member_count=member_count,
                    total_distance_meters=int(total_distance_meters),
                ),
            )
        return result
    except SQLAlchemyError as err:
        raise _internal_server_error(err, "get_challenges_for_user") from err


def create_challenge(db: Session, payload: challenges_schema.ChallengeCreate, user_id: int) -> challenges_schema.ChallengeRead:
    """Create a challenge and return the persisted record summary."""

    try:
        challenge = challenges_models.Challenge(
            name=payload.name,
            start_date=payload.start_date,
            end_date=payload.end_date,
            created_by_user_id=user_id,
        )
        db.add(challenge)
        db.commit()
        db.refresh(challenge)
        return challenges_schema.ChallengeRead(
            id=challenge.id,
            name=challenge.name,
            start_date=challenge.start_date,
            end_date=challenge.end_date,
            created_by_user_id=challenge.created_by_user_id,
            member_count=0,
            total_distance_meters=0,
        )
    except SQLAlchemyError as err:
        db.rollback()
        raise _internal_server_error(err, "create_challenge") from err


def delete_challenge(db: Session, challenge_id: int, user_id: int) -> None:
    """Delete a challenge when the caller owns it."""

    challenge = db.execute(
        select(challenges_models.Challenge).where(challenges_models.Challenge.id == challenge_id),
    ).scalar_one_or_none()
    if challenge is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found")
    if challenge.created_by_user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the challenge owner can delete it")

    try:
        db.execute(delete(challenges_models.Challenge).where(challenges_models.Challenge.id == challenge_id))
        db.commit()
    except SQLAlchemyError as err:
        db.rollback()
        raise _internal_server_error(err, "delete_challenge") from err


def get_challenge_members(db: Session, challenge_id: int) -> list[challenges_schema.ChallengeMemberRead]:
    """Return every member in the challenge with their challenge-window mileage."""

    challenge = db.execute(
        select(challenges_models.Challenge).where(challenges_models.Challenge.id == challenge_id),
    ).scalar_one_or_none()
    if challenge is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found")

    try:
        rows = db.execute(
            select(
                challenges_models.ChallengeMember.user_id,
                users_models.Users.name,
                users_models.Users.username,
                func.coalesce(func.sum(activity_models.Activity.distance), 0),
            )
            .select_from(challenges_models.ChallengeMember)
            .join(users_models.Users, users_models.Users.id == challenges_models.ChallengeMember.user_id)
            .outerjoin(
                activity_models.Activity,
                and_(
                    activity_models.Activity.user_id == challenges_models.ChallengeMember.user_id,
                    activity_models.Activity.start_time >= datetime.combine(challenge.start_date, datetime.min.time(), tzinfo=UTC),
                    activity_models.Activity.start_time < datetime.combine(challenge.end_date, datetime.min.time(), tzinfo=UTC),
                ),
            )
            .where(challenges_models.ChallengeMember.challenge_id == challenge_id)
            .group_by(
                challenges_models.ChallengeMember.user_id,
                users_models.Users.name,
                users_models.Users.username,
            )
            .order_by(challenges_models.ChallengeMember.user_id),
        ).all()
        result: list[challenges_schema.ChallengeMemberRead] = []
        for user_id, name, username, total_distance_meters in rows:
            result.append(
                challenges_schema.ChallengeMemberRead(
                    user_id=user_id,
                    name=name,
                    username=username,
                    total_distance_meters=int(total_distance_meters),
                ),
            )
        return result
    except SQLAlchemyError as err:
        raise _internal_server_error(err, "get_challenge_members") from err


def join_challenge(db: Session, challenge_id: int, user_id: int) -> challenges_schema.ChallengeMembershipStatus:
    """Add the current user to a challenge."""

    challenge = db.execute(
        select(challenges_models.Challenge).where(challenges_models.Challenge.id == challenge_id),
    ).scalar_one_or_none()
    if challenge is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found")

    membership = db.execute(
        select(challenges_models.ChallengeMember).where(
            challenges_models.ChallengeMember.challenge_id == challenge_id,
            challenges_models.ChallengeMember.user_id == user_id,
        ),
    ).scalar_one_or_none()
    if membership is not None:
        return challenges_schema.ChallengeMembershipStatus(
            challenge_id=challenge_id,
            user_id=user_id,
            joined=True,
            joined_at=membership.joined_at,
        )

    try:
        membership = challenges_models.ChallengeMember(
            challenge_id=challenge_id,
            user_id=user_id,
        )
        db.add(membership)
        db.commit()
        db.refresh(membership)
        return challenges_schema.ChallengeMembershipStatus(
            challenge_id=challenge_id,
            user_id=user_id,
            joined=True,
            joined_at=membership.joined_at,
        )
    except SQLAlchemyError as err:
        db.rollback()
        raise _internal_server_error(err, "join_challenge") from err


def leave_challenge(db: Session, challenge_id: int, user_id: int) -> None:
    """Remove the current user from a challenge."""

    try:
        db.execute(
            delete(challenges_models.ChallengeMember).where(
                challenges_models.ChallengeMember.challenge_id == challenge_id,
                challenges_models.ChallengeMember.user_id == user_id,
            ),
        )
        db.commit()
    except SQLAlchemyError as err:
        db.rollback()
        raise _internal_server_error(err, "leave_challenge") from err


def get_membership_status(db: Session, challenge_id: int, user_id: int) -> challenges_schema.ChallengeMembershipStatus:
    """Return whether the current user already belongs to the challenge."""

    membership = db.execute(
        select(challenges_models.ChallengeMember).where(
            challenges_models.ChallengeMember.challenge_id == challenge_id,
            challenges_models.ChallengeMember.user_id == user_id,
        ),
    ).scalar_one_or_none()
    return challenges_schema.ChallengeMembershipStatus(
        challenge_id=challenge_id,
        user_id=user_id,
        joined=membership is not None,
        joined_at=membership.joined_at if membership is not None else None,
    )
