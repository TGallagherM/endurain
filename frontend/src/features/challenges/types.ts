export interface ChallengeSummary {
  id: number
  name: string
  startDate: string
  endDate: string
  createdByUserId: number
  memberCount: number
  totalDistanceMeters: number
}

export interface ChallengeMemberSummary {
  userId: number
  name: string | null
  username: string | null
  totalDistanceMeters: number
}

export interface ChallengeMembershipStatus {
  challengeId: number
  userId: number
  joined: boolean
  joinedAt: string | null
}
