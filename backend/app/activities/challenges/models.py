"""Fitness challenge database models."""

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base

if TYPE_CHECKING:
    from users.users.models import Users


class Challenge(Base):
    """
    Fitness challenge definition.

    Attributes:
        id: Primary key.
        name: Challenge display name.
        start_date: Inclusive challenge start date.
        end_date: Inclusive challenge end date.
        created_by_user_id: Challenge owner.
        challenge_members: Membership rows tied to the challenge.
    """

    __tablename__ = "challenges"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(length=250), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    challenge_members: Mapped[list["ChallengeMember"]] = relationship(
        back_populates="challenge",
        cascade="all, delete-orphan",
    )
    creator: Mapped["Users"] = relationship("Users", foreign_keys=[created_by_user_id])


class ChallengeMember(Base):
    """
    Membership row linking a user to a challenge.

    Attributes:
        challenge_id: Challenge the member belongs to.
        user_id: User participating in the challenge.
        joined_at: Time the user joined the challenge.
        challenge: Parent challenge.
        user: Owner user.
    """

    __tablename__ = "challenge_members"
    __table_args__ = (
        UniqueConstraint("challenge_id", "user_id", name="uq_challenge_member"),
    )

    challenge_id: Mapped[int] = mapped_column(
        ForeignKey("challenges.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    challenge: Mapped["Challenge"] = relationship(back_populates="challenge_members")
    user: Mapped["Users"] = relationship("Users", foreign_keys=[user_id])
