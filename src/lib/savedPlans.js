import { supabase } from './supabase.js'

function mapRowToSavedPlan(row) {
  return {
    id: row.id,
    savedAt: row.saved_at,
    summary: row.summary,
    metadata: row.metadata ?? {},
    days: row.days ?? [],
    optionalDays: row.optional_days ?? [],
    coachingNotes: row.coaching_notes ?? [],
    athleteSnapshot: row.athlete_snapshot ?? [],
    intake: row.intake ?? {},
  }
}

export async function fetchSavedPlans(userId) {
  const { data, error } = await supabase
    .from('saved_plans')
    .select(
      'id, saved_at, summary, metadata, days, optional_days, coaching_notes, athlete_snapshot, intake'
    )
    .eq('user_id', userId)
    .order('saved_at', { ascending: false })

  if (error) {
    throw error
  }

  return (data ?? []).map(mapRowToSavedPlan)
}

export async function createSavedPlan(userId, plan, intake) {
  const payload = {
    user_id: userId,
    summary: plan.summary,
    metadata: plan.metadata,
    days: plan.days,
    optional_days: plan.optional_days ?? [],
    coaching_notes: plan.coaching_notes,
    athlete_snapshot: plan.athlete_snapshot,
    intake,
  }

  const { data, error } = await supabase
    .from('saved_plans')
    .insert(payload)
    .select(
      'id, saved_at, summary, metadata, days, optional_days, coaching_notes, athlete_snapshot, intake'
    )
    .single()

  if (error) {
    throw error
  }

  return mapRowToSavedPlan(data)
}

export async function deleteSavedPlan(userId, planId) {
  const { error } = await supabase
    .from('saved_plans')
    .delete()
    .eq('user_id', userId)
    .eq('id', planId)

  if (error) {
    throw error
  }
}
