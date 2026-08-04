<script setup lang="ts">
import { computed, ref, unref } from 'vue'
import { Plus } from '@lucide/vue'

import { Button } from '@/components/ui/button'
import { EmptyState } from '@/components/ui/empty-state'
import { ListPanel } from '@/components/ui/list-panel'
import { Skeleton } from '@/components/ui/skeleton'
import { useCurrentUser } from '@/features/auth/composables/useCurrentUser'
import { formatDistance } from '@/features/activities/utils/format'
import { useDisplayUnits } from '@/features/activities/composables/useActivityDetail'
import {
  useChallengeMembersQuery,
  useChallengeMembershipStatusQuery,
  useChallengesQuery,
  useCreateChallengeMutation,
  useDeleteChallengeMutation,
  useChallengeMembershipMutation,
} from '@/features/challenges/composables/useChallenges'

const units = useDisplayUnits()

const selectedChallengeId = ref<number | null>(null)
const createName = ref('')
const createStartDate = ref('')
const createEndDate = ref('')

const { data: currentUser } = useCurrentUser()
const challengesQuery = useChallengesQuery()
const createMutation = useCreateChallengeMutation()
const deleteMutation = useDeleteChallengeMutation()
const membershipMutation = useChallengeMembershipMutation()
const membersQuery = useChallengeMembersQuery(computed(() => selectedChallengeId.value))
const membershipStatusQuery = useChallengeMembershipStatusQuery(
  computed(() => selectedChallengeId.value),
  computed(() => currentUser.value?.id ?? null),
)

const challenges = computed(() => challengesQuery.data.value ?? [])
const members = computed(() => membersQuery.data.value ?? [])
const isCurrentUserJoined = computed(() => membershipStatusQuery.data.value?.joined ?? false)

const selectedChallenge = computed(() =>
  challenges.value.find((challenge) => challenge.id === selectedChallengeId.value) ?? null,
)

function selectChallenge(challengeId: number): void {
  selectedChallengeId.value = challengeId
}

function createChallenge(): void {
  if (!createName.value.trim() || !createStartDate.value || !createEndDate.value) {
    return
  }
  createMutation.mutate({
    name: createName.value.trim(),
    startDate: createStartDate.value,
    endDate: createEndDate.value,
  })
}

function removeChallenge(challengeId: number): void {
  deleteMutation.mutate(challengeId)
}

function renderDistance(meters: number | null | undefined): string {
  const distanceValue = meters ?? 0
  const formatted = formatDistance(distanceValue, 1, unref(units))
  return `${formatted.value} ${formatted.unit}`
}

function toggleMembership(challengeId: number, active: boolean): void {
  membershipMutation.mutate({ challengeId, action: active ? 'leave' : 'join' })
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 class="text-page-title">Fitness challenges</h1>
        <p class="text-body">Manage challenge windows, team participation, and mileage totals.</p>
      </div>
    </div>

    <div class="grid gap-4 xl:grid-cols-[360px_minmax(0,1fr)]">
      <ListPanel
        :is-loading="challengesQuery.isPending.value"
        :is-error="challengesQuery.isError.value"
        :is-empty="!challengesQuery.isPending.value && !challengesQuery.isError.value && challenges.length === 0"
        error-title="Unable to load challenges"
        retry-label="Retry"
      >
        <template #header>
          <div class="flex items-center justify-between gap-3 px-4 py-3">
            <Skeleton v-if="challengesQuery.isPending.value" class="h-4 w-32" />
            <p v-else class="text-hint">{{ challenges.length }} challenges</p>
          </div>
        </template>

        <template #empty>
          <EmptyState title="No challenges yet" description="Create a challenge to begin tracking team mileage.">
            <template #icon>
              <Plus class="size-8" aria-hidden="true" />
            </template>
          </EmptyState>
        </template>

        <ul class="divide-y divide-border">
          <li v-for="challenge in challenges" :key="challenge.id">
            <button
              class="flex w-full flex-col gap-1 px-4 py-3 text-left"
              @click="selectChallenge(challenge.id)"
            >
              <span class="text-item-title">{{ challenge.name }}</span>
              <span class="text-caption">{{ challenge.startDate }} → {{ challenge.endDate }}</span>
              <span class="text-caption">{{ challenge.memberCount }} members · {{ renderDistance(challenge.totalDistanceMeters) }}</span>
            </button>
            <div class="px-4 pb-3">
              <Button variant="outline" size="sm" @click="removeChallenge(challenge.id)">Delete</Button>
            </div>
          </li>
        </ul>
      </ListPanel>

      <div class="rounded-card border border-border bg-background p-4">
        <div class="grid gap-3 md:grid-cols-3">
          <label class="flex flex-col gap-1">
            <span class="text-caption">Challenge name</span>
            <input v-model="createName" class="rounded-input border border-border bg-background px-3 py-2" />
          </label>
          <label class="flex flex-col gap-1">
            <span class="text-caption">Start date</span>
            <input v-model="createStartDate" type="date" class="rounded-input border border-border bg-background px-3 py-2" />
          </label>
          <label class="flex flex-col gap-1">
            <span class="text-caption">End date</span>
            <input v-model="createEndDate" type="date" class="rounded-input border border-border bg-background px-3 py-2" />
          </label>
        </div>
        <div class="mt-3">
          <Button @click="createChallenge">Create challenge</Button>
        </div>

        <div v-if="selectedChallenge" class="mt-6">
          <div class="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 class="text-section-heading">{{ selectedChallenge.name }}</h2>
              <p class="text-body">{{ selectedChallenge.startDate }} → {{ selectedChallenge.endDate }}</p>
              <p class="text-caption mt-2">Cumulative team distance: {{ renderDistance(selectedChallenge.totalDistanceMeters) }}</p>
            </div>
            <Button
              variant="outline"
              size="sm"
              @click="toggleMembership(selectedChallenge.id, isCurrentUserJoined)"
            >
              {{ isCurrentUserJoined ? 'Leave challenge' : 'Join challenge' }}
            </Button>
          </div>

          <div class="mt-4 grid gap-3">
            <div v-for="member in members" :key="member.userId" class="flex items-center justify-between rounded-input border border-border px-3 py-2">
              <div>
                <p class="text-item-title">{{ member.name ?? member.username ?? `User ${member.userId}` }}</p>
                <p class="text-caption">{{ renderDistance(member.totalDistanceMeters) }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
