"""Fitness challenge Pydantic schemas."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr


class ChallengeCreate(BaseModel):
    """Schema for creating a new fitness challenge."""

    name: StrictStr = Field(..., min_length=1, max_length=250, description="Challenge display name")
    start_date: date = Field(..., description="Inclusive challenge start date")
    end_date: date = Field(..., description="Inclusive challenge end date")

    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
        validate_assignment=True,
    )


class ChallengeRead(BaseModel):
    """Schema for reading one challenge."""

    id: StrictInt = Field(..., ge=1, description="Challenge identifier")
    name: StrictStr = Field(..., description="Challenge display name")
    start_date: date = Field(..., description="Inclusive challenge start date")
    end_date: date = Field(..., description="Inclusive challenge end date")
    created_by_user_id: StrictInt = Field(..., ge=1, description="Creating user identifier")
    member_count: StrictInt = Field(default=0, ge=0, description="Number of participating team members")
    total_distance_meters: StrictInt = Field(default=0, ge=0, description="Challenge window distance total")

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class ChallengeMemberRead(BaseModel):
    """Schema for a member included in a challenge."""

    user_id: StrictInt = Field(..., ge=1, description="Participating user identifier")
    name: StrictStr | None = Field(default=None, description="User display name")
    username: StrictStr | None = Field(default=None, description="Username")
    total_distance_meters: StrictInt = Field(default=0, ge=0, description="Challenge window distance total")

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class ChallengeMembershipStatus(BaseModel):
    """Schema describing the current membership state for a challenge."""

    challenge_id: StrictInt = Field(..., ge=1, description="Challenge identifier")
    user_id: StrictInt = Field(..., ge=1, description="User identifier")
    joined: bool = Field(default=False, description="Whether the current user is participating")
    joined_at: datetime | None = Field(default=None, description="Timestamp when the user joined")

    model_config = ConfigDict(from_attributes=True, extra="forbid")
