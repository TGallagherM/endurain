import { computed, type MaybeRefOrGetter, toValue } from 'vue'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'

import type { ChallengeMemberSummary, ChallengeMembershipStatus, ChallengeSummary } from '@/features/challenges/types'

import { queryKeys } from '@/services/queryKeys'
import { useAuthStore } from '@/features/auth/stores/auth'
import {
  createChallenge,
  deleteChallenge,
  fetchChallengeMembers,
  fetchChallengeMembershipStatus,
  fetchChallenges,
  joinChallenge,
  leaveChallenge,
} from '@/features/challenges/services/challenges'

/**
 * Fetches the challenge list for the signed-in user's team view.
 */
export function useChallengesQuery() {
  const { isAuthenticated } = useAuthStore()

  return useQuery<ChallengeSummary[]>({
    queryKey: queryKeys.activities.challenges(),
    queryFn: ({ signal }) => fetchChallenges(signal),
    enabled: computed(() => isAuthenticated),
    staleTime: 5 * 60_000,
  })
}

/**
 * Fetches the competition roster for one challenge.
 *
 * @param challengeId - Reactive challenge identifier.
 */
export function useChallengeMembersQuery(challengeId: MaybeRefOrGetter<number | null>) {
  const { isAuthenticated } = useAuthStore()
  const id = computed(() => toValue(challengeId))

  return useQuery<ChallengeMemberSummary[]>({
    // queryKey: computed(() => (id.value ? queryKeys.activities.challengeMembers(id.value) : queryKeys.activities.challenges())),
    queryKey: computed(() => queryKeys.activities.challengeMembers(id.value ?? 0)),
    queryFn: ({ signal }) => {
      const resolved = toValue(challengeId)
      if (resolved === null || resolved <= 0) {
        return Promise.resolve([])
      }
      return fetchChallengeMembers(resolved, signal)
    },
    enabled: computed(() => isAuthenticated && id.value !== null && id.value > 0),
    staleTime: 5 * 60_000,
  })
}

/**
 * Fetches the signed-in user's membership state for one selected challenge.
 *
 * @param challengeId - Reactive challenge identifier.
 * @param userId - Reactive user identifier.
 */
export function useChallengeMembershipStatusQuery(
  challengeId: MaybeRefOrGetter<number | null>,
  userId: MaybeRefOrGetter<number | null>,
) {
  const { isAuthenticated } = useAuthStore()
  const resolvedChallengeId = computed(() => toValue(challengeId))
  const resolvedUserId = computed(() => toValue(userId))

  return useQuery<ChallengeMembershipStatus>({
    // queryKey: computed(() =>
    //   resolvedChallengeId.value && resolvedUserId.value
    //     ? queryKeys.activities.challengeMembershipStatus(resolvedChallengeId.value, resolvedUserId.value)
    //     : queryKeys.activities.challenges(),
    // ),
    queryKey: computed(() =>
    queryKeys.activities.challengeMembershipStatus(
        resolvedChallengeId.value ?? 0,
        resolvedUserId.value ?? 0,
      ),
    ),
    queryFn: ({ signal }) => {
      const challengeValue = toValue(challengeId)
      const userValue = toValue(userId)
      if (challengeValue === null || challengeValue <= 0 || userValue === null || userValue <= 0) {
        return Promise.resolve({
          challengeId: 0,
          userId: 0,
          joined: false,
          joinedAt: null,
        })
      }
      return fetchChallengeMembershipStatus(challengeValue, userValue, signal)
    },
    enabled: computed(() => isAuthenticated && resolvedChallengeId.value !== null && resolvedChallengeId.value > 0),
    staleTime: 5 * 60_000,
  })
}

/**
 * Creates a new challenge and refreshes the activity-challenge list cache.
 */
export function useCreateChallengeMutation() {
  const client = useQueryClient()

  return useMutation({
    mutationFn: createChallenge,
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: queryKeys.activities.challenges() })
    },
  })
}

/**
 * Deletes a challenge and refreshes the challenge list cache.
 */
export function useDeleteChallengeMutation() {
  const client = useQueryClient()

  return useMutation({
    mutationFn: deleteChallenge,
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: queryKeys.activities.challenges() })
    },
  })
}

/**
 * Joins or leaves a challenge and refreshes the memberships list.
 */
export function useChallengeMembershipMutation() {
  const client = useQueryClient()

  return useMutation({
    mutationFn: async ({ challengeId, action }: { challengeId: number; action: 'join' | 'leave' }) => {
      if (action === 'join') {
        return joinChallenge(challengeId)
      }
      await leaveChallenge(challengeId)
      return undefined
    },
    onSuccess: (_data, variables) => {
      void client.invalidateQueries({ queryKey: queryKeys.activities.challenges() })
      void client.invalidateQueries({ queryKey: queryKeys.activities.challengeMembers(variables.challengeId) })
    },
  })
}
