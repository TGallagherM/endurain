import type { ChallengeMemberSummary, ChallengeMembershipStatus, ChallengeSummary } from '@/features/challenges/types'

import { apiFetch } from '@/services/http'

/**
 * Maps the raw challenge DTO from the backend into the clean client model used
 * by the view.
 *
 * @param dto - Raw challenge payload from the backend.
 * @returns The normalized challenge summary.
 */
export function mapChallenge(dto: {
  id: number
  name: string
  start_date: string
  end_date: string
  created_by_user_id: number
  member_count: number
  total_distance_meters: number
}): ChallengeSummary {
  return {
    id: dto.id,
    name: dto.name,
    startDate: dto.start_date,
    endDate: dto.end_date,
    createdByUserId: dto.created_by_user_id,
    memberCount: dto.member_count,
    totalDistanceMeters: dto.total_distance_meters,
  }
}

/**
 * Maps a challenge-member DTO that returns user + distance rollups.
 *
 * @param dto - Raw backend member payload.
 * @returns The normalized member model.
 */
export function mapChallengeMember(dto: {
  user_id: number
  name: string | null
  username: string | null
  total_distance_meters: number
}): ChallengeMemberSummary {
  return {
    userId: dto.user_id,
    name: dto.name,
    username: dto.username,
    totalDistanceMeters: dto.total_distance_meters,
  }
}

/**
 * Fetches the full challenge list for the authenticated user.
 *
 * @param signal - Optional abort signal.
 * @returns The challenge summary list.
 */
export async function fetchChallenges(signal?: AbortSignal): Promise<ChallengeSummary[]> {
  const dtos = await apiFetch<
    {
      id: number
      name: string
      start_date: string
      end_date: string
      created_by_user_id: number
      member_count: number
      total_distance_meters: number
    }[] | null
  >('/activities/challenges', { signal })
  return (dtos ?? []).map(mapChallenge)
}

/**
 * Fetches all members currently competing in the selected challenge.
 *
 * @param challengeId - Challenge identifier.
 * @param signal - Optional abort signal.
 * @returns Member distance summaries.
 */
export async function fetchChallengeMembers(
  challengeId: number,
  signal?: AbortSignal,
): Promise<ChallengeMemberSummary[]> {
  const dtos = await apiFetch<
    {
      user_id: number
      name: string | null
      username: string | null
      total_distance_meters: number
    }[] | null
  >(`/activities/challenges/${challengeId}/members`, { signal })
  return (dtos ?? []).map(mapChallengeMember)
}

/**
 * Fetches the signed-in user's membership state for one challenge.
 *
 * @param challengeId - Challenge identifier.
 * @param userId - User identifier.
 * @param signal - Optional abort signal.
 * @returns The membership state payload.
 */
export async function fetchChallengeMembershipStatus(
  challengeId: number,
  userId: number,
  signal?: AbortSignal,
): Promise<ChallengeMembershipStatus> {
  const dto = await apiFetch<{
    challenge_id: number
    user_id: number
    joined: boolean
    joined_at: string | null
  }>(`/activities/challenges/${challengeId}/members/${userId}/status`, { signal })

  return {
    challengeId: dto.challenge_id,
    userId: dto.user_id,
    joined: dto.joined,
    joinedAt: dto.joined_at,
  }
}

/**
 * Creates a new challenge for the authenticated user.
 *
 * @param input - Create payload.
 * @returns The created challenge summary.
 */
export async function createChallenge(input: {
  name: string
  startDate: string
  endDate: string
}): Promise<ChallengeSummary> {
  const dto = await apiFetch<{
    id: number
    name: string
    start_date: string
    end_date: string
    created_by_user_id: number
    member_count: number
    total_distance_meters: number
  }>('/activities/challenges', {
    method: 'POST',
    body: JSON.stringify({
      name: input.name,
      start_date: input.startDate,
      end_date: input.endDate,
    }),
  })
  return mapChallenge(dto)
}

/**
 * Deletes a challenge owned by the current user.
 *
 * @param challengeId - Challenge identifier.
 */
export async function deleteChallenge(challengeId: number): Promise<void> {
  await apiFetch(`/activities/challenges/${challengeId}`, {
    method: 'DELETE',
    responseType: 'void',
  })
}

/**
 * Joins the authenticated user to a challenge.
 *
 * @param challengeId - Challenge identifier.
 * @returns The resulting membership-state payload.
 */
export async function joinChallenge(challengeId: number): Promise<ChallengeMembershipStatus> {
  const dto = await apiFetch<{
    challenge_id: number
    user_id: number
    joined: boolean
    joined_at: string | null
  }>(`/activities/challenges/${challengeId}/join`, {
    method: 'POST',
  })
  return {
    challengeId: dto.challenge_id,
    userId: dto.user_id,
    joined: dto.joined,
    joinedAt: dto.joined_at,
  }
}

/**
 * Removes the authenticated user from a challenge.
 *
 * @param challengeId - Challenge identifier.
 */
export async function leaveChallenge(challengeId: number): Promise<void> {
  await apiFetch(`/activities/challenges/${challengeId}/join`, {
    method: 'DELETE',
    responseType: 'void',
  })
}
