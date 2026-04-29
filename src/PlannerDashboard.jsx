import { useEffect, useMemo, useState } from 'react'
import {
  createSavedPlan,
  deleteSavedPlan,
  fetchSavedPlans,
  updateSavedPlan,
} from './lib/savedPlans.js'

const experienceLevels = ['Beginner', 'Intermediate', 'Advanced']
const equipmentOptions = [
  'Bodyweight',
  'Dumbbells',
  'Resistance bands',
  'Bench',
  'Barbell / rack',
  'Machines / cables',
  'Cardio equipment',
  'Kettlebells',
  'Pull-up bar',
  'Mat / floor space',
]
const ageRanges = ['18-24', '25-34', '35-44', '45-54', '55+']
const activityLevels = [
  'Mostly sedentary',
  'Lightly active',
  'Moderately active',
  'Very active',
]
const intensityPreferences = ['Light', 'Moderate', 'Challenging']
const weekDays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
const navItems = [
  { id: 'home', label: 'Home' },
  { id: 'generate', label: 'AI Planner' },
  { id: 'saved', label: 'Saved Plans' },
  { id: 'edit', label: 'Edit Plan' },
  { id: 'profile', label: 'Profile' },
]

const panelClass =
  'relative overflow-hidden rounded-[28px] border border-white/10 bg-[rgba(15,19,21,0.74)] p-5 shadow-[0_24px_90px_rgba(0,0,0,0.24)] backdrop-blur-xl md:p-7'

const panelGlowClass =
  "before:pointer-events-none before:absolute before:inset-0 before:bg-[linear-gradient(135deg,rgba(255,255,255,0.08),transparent_40%)] before:content-['']"

const sectionLabelClass =
  'text-[0.72rem] uppercase tracking-[0.14em] text-[#c2b7a6]'

const cardClass = 'rounded-[22px] border border-white/10 bg-white/[0.03]'

const inputClass =
  'w-full rounded-[18px] border border-white/12 bg-white/[0.04] px-4 py-3.5 text-[#f5efe4] outline-none transition focus:border-[#ffb37c]/50 focus:ring-2 focus:ring-[#f08f56]/20'

function clampNumber(value, fallback, minimum, maximum) {
  const numericValue = Number(value)
  if (!Number.isFinite(numericValue)) {
    return fallback
  }

  return Math.min(Math.max(Math.round(numericValue), minimum), maximum)
}

function normalizeSavedPlanIntake(intake = {}, fallbackDays = []) {
  const availableTrainingDays = Array.isArray(
    intake.available_training_days ?? intake.availableTrainingDays
  )
    ? (intake.available_training_days ?? intake.availableTrainingDays).filter(Boolean)
    : fallbackDays

  const daysPerWeek = clampNumber(
    intake.days_per_week ?? intake.daysPerWeek ?? availableTrainingDays.length,
    Math.max(2, availableTrainingDays.length || 2),
    2,
    7
  )

  const sessionLengthMax = clampNumber(
    intake.session_length_max ?? intake.sessionLengthMax,
    45,
    20,
    90
  )

  const sessionLengthMin = clampNumber(
    intake.session_length_min ?? intake.sessionLengthMin ?? sessionLengthMax,
    sessionLengthMax,
    20,
    90
  )

  return {
    experience: intake.experience ?? experienceLevels[0],
    equipment: Array.isArray(intake.equipment) && intake.equipment.length > 0
      ? intake.equipment
      : ['Bodyweight'],
    age_range: intake.age_range ?? intake.ageRange ?? ageRanges[0],
    days_per_week: daysPerWeek,
    session_length_min: Math.min(sessionLengthMin, sessionLengthMax),
    session_length_max: sessionLengthMax,
    available_training_days:
      availableTrainingDays.length > 0 ? availableTrainingDays.slice(0, 7) : weekDays.slice(0, daysPerWeek),
    injuries: intake.injuries ?? '',
    current_activity_level:
      intake.current_activity_level ?? intake.currentActivityLevel ?? activityLevels[0],
    intensity_preference:
      intake.intensity_preference ?? intake.intensityPreference ?? intensityPreferences[0],
    notes: intake.notes ?? '',
  }
}

function normalizeSavedExercise(exercise = {}) {
  return {
    name: exercise.name ?? '',
    sets: clampNumber(exercise.sets, 3, 1, 8),
    reps: exercise.reps ?? '',
    rest_seconds: clampNumber(exercise.rest_seconds ?? exercise.restSeconds, 60, 15, 240),
    intensity_note: exercise.intensity_note ?? exercise.intensityNote ?? '',
    primary_muscle_group:
      exercise.primary_muscle_group ?? exercise.primaryMuscleGroup ?? '',
    secondary_muscles: Array.isArray(
      exercise.secondary_muscles ?? exercise.secondaryMuscles
    )
      ? (exercise.secondary_muscles ?? exercise.secondaryMuscles).slice(0, 5)
      : [],
    movement_pattern: exercise.movement_pattern ?? exercise.movementPattern ?? '',
    equipment_used: exercise.equipment_used ?? exercise.equipmentUsed ?? '',
    coaching_cues: Array.isArray(exercise.coaching_cues ?? exercise.coachingCues)
      ? (exercise.coaching_cues ?? exercise.coachingCues).slice(0, 3)
      : [],
    exercise_explanation:
      exercise.exercise_explanation ?? exercise.exerciseExplanation ?? '',
    substitution_note: exercise.substitution_note ?? exercise.substitutionNote ?? '',
  }
}

function normalizeSavedPlanDay(day = {}) {
  return {
    day: day.day ?? '',
    focus: day.focus ?? '',
    duration_minutes: clampNumber(day.duration_minutes ?? day.durationMinutes, 45, 1, 90),
    warmup: Array.isArray(day.warmup) ? day.warmup.slice(0, 5) : [],
    exercises: Array.isArray(day.exercises)
      ? day.exercises.map((exercise) => normalizeSavedExercise(exercise)).slice(0, 6)
      : [],
    cooldown: Array.isArray(day.cooldown) ? day.cooldown.slice(0, 3) : [],
    coach_notes: Array.isArray(day.coach_notes ?? day.coachNotes)
      ? (day.coach_notes ?? day.coachNotes).slice(0, 3)
      : [],
  }
}

function PlannerDashboard({ userId, userEmail, onSignOut }) {
  const [activePage, setActivePage] = useState('home')
  const [experience, setExperience] = useState(experienceLevels[0])
  const [equipment, setEquipment] = useState(['Bodyweight', 'Dumbbells', 'Bench'])
  const [ageRange, setAgeRange] = useState(ageRanges[1])
  const [activityLevel, setActivityLevel] = useState(activityLevels[1])
  const [intensityPreference, setIntensityPreference] = useState(intensityPreferences[1])
  const [sessionLengthMax, setSessionLengthMax] = useState(50)
  const [trainingDays, setTrainingDays] = useState(['Monday', 'Wednesday', 'Friday', 'Saturday'])
  const [injuries, setInjuries] = useState('')
  const [notes, setNotes] = useState('')
  const [generatedPlan, setGeneratedPlan] = useState(null)
  const [savedPlans, setSavedPlans] = useState([])
  const [expandedSavedPlans, setExpandedSavedPlans] = useState({})
  const [expandedSavedPlanDays, setExpandedSavedPlanDays] = useState({})
  const [isLoadingSavedPlans, setIsLoadingSavedPlans] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState('')
  const [saveMessage, setSaveMessage] = useState('')
  const [savedPlansError, setSavedPlansError] = useState('')
  const [renamingPlanId, setRenamingPlanId] = useState(null)
  const [renamingTitle, setRenamingTitle] = useState('')
  const [isSavingPlanTitle, setIsSavingPlanTitle] = useState(false)
  const [planBeingEdited, setPlanBeingEdited] = useState(null)
  const [editInstructions, setEditInstructions] = useState('')
  const [selectedEditSessions, setSelectedEditSessions] = useState({})
  const [selectedEditExercises, setSelectedEditExercises] = useState({})
  const [editedPlanDraft, setEditedPlanDraft] = useState(null)
  const [isSubmittingEdit, setIsSubmittingEdit] = useState(false)
  const [isSavingEditedPlan, setIsSavingEditedPlan] = useState(false)
  const [editPlanError, setEditPlanError] = useState('')
  const [editPlanMessage, setEditPlanMessage] = useState('')

  useEffect(() => {
    let isMounted = true

    async function loadSavedPlans() {
      setIsLoadingSavedPlans(true)
      setSavedPlansError('')

      try {
        const plans = await fetchSavedPlans(userId)
        if (isMounted) {
          setSavedPlans(plans)
        }
      } catch (error) {
        if (isMounted) {
          setSavedPlansError(
            error instanceof Error ? error.message : 'Could not load saved plans.'
          )
        }
      } finally {
        if (isMounted) {
          setIsLoadingSavedPlans(false)
        }
      }
    }

    loadSavedPlans()

    return () => {
      isMounted = false
    }
  }, [userId])

  const selectedTrainingDays = useMemo(() => trainingDays, [trainingDays])
  const daysPerWeek = selectedTrainingDays.length

  const payloadPreview = useMemo(
    () => ({
      experience,
      equipment,
      age_range: ageRange,
      days_per_week: daysPerWeek,
      session_length_min: sessionLengthMax,
      session_length_max: sessionLengthMax,
      available_training_days: selectedTrainingDays,
      injuries,
      current_activity_level: activityLevel,
      intensity_preference: intensityPreference,
      notes,
    }),
    [
      activityLevel,
      ageRange,
      daysPerWeek,
      equipment,
      experience,
      intensityPreference,
      injuries,
      notes,
      selectedTrainingDays,
      sessionLengthMax,
    ]
  )

  const profileStats = [
    { label: 'Current setup', value: equipment.join(', ') },
    { label: 'Training rhythm', value: `${daysPerWeek} days · up to ${sessionLengthMax} min` },
    { label: 'Baseline activity', value: activityLevel },
    { label: 'Planning preferences', value: intensityPreference },
  ]

  function toggleEquipment(option) {
    setEquipment((currentEquipment) => {
      if (currentEquipment.includes(option)) {
        if (currentEquipment.length <= 1) {
          return currentEquipment
        }

        return currentEquipment.filter((item) => item !== option)
      }

      return [...currentEquipment, option]
    })
  }

  function toggleTrainingDay(day) {
    setTrainingDays((currentDays) => {
      if (currentDays.includes(day)) {
        if (currentDays.length <= 2) {
          return currentDays
        }

        return currentDays.filter((item) => item !== day)
      }

      if (currentDays.length >= 7) {
        return currentDays
      }

      return [...currentDays, day]
    })
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setIsSubmitting(true)
    setSubmitError('')
    setSaveMessage('')

    try {
      const response = await fetch('/api/plan', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payloadPreview),
      })

      const data = await response.json()

      if (!response.ok) {
        const detail =
          typeof data?.detail === 'string'
            ? data.detail
            : data?.error || 'Plan generation failed.'
        throw new Error(detail)
      }

      setGeneratedPlan(data)
      setActivePage('generate')
    } catch (error) {
      setSubmitError(error instanceof Error ? error.message : 'Something went wrong.')
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleSavePlan() {
    if (!generatedPlan) {
      return
    }

    try {
      const savedPlan = await createSavedPlan(userId, generatedPlan, payloadPreview)
      setSavedPlans((currentPlans) => [savedPlan, ...currentPlans])
      setSavedPlansError('')
      setSaveMessage('Plan saved to Supabase.')
      setActivePage('saved')
    } catch (error) {
      setSaveMessage('')
      setSavedPlansError(error instanceof Error ? error.message : 'Could not save plan.')
    }
  }

  async function handleDeleteSavedPlan(planId) {
    try {
      await deleteSavedPlan(userId, planId)
      setSavedPlans((currentPlans) => currentPlans.filter((plan) => plan.id !== planId))
      setSavedPlansError('')
    } catch (error) {
      setSavedPlansError(error instanceof Error ? error.message : 'Could not delete plan.')
    }
  }

  function handleStartRenameSavedPlan(plan) {
    setRenamingPlanId(plan.id)
    setRenamingTitle(plan.summary)
    setSavedPlansError('')
    setSaveMessage('')
  }

  function handleCancelRenameSavedPlan() {
    setRenamingPlanId(null)
    setRenamingTitle('')
  }

  async function handleSaveSavedPlanTitle(plan) {
    const trimmedTitle = renamingTitle.trim()
    if (!trimmedTitle || trimmedTitle === plan.summary) {
      handleCancelRenameSavedPlan()
      return
    }

    setIsSavingPlanTitle(true)
    setSavedPlansError('')
    setSaveMessage('')

    try {
      const updatedPlan = await updateSavedPlan(
        userId,
        plan.id,
        {
          ...mapSavedPlanToApiPlan(plan),
          summary: trimmedTitle,
        },
        plan.intake
      )

      setSavedPlans((currentPlans) =>
        currentPlans.map((item) => (item.id === updatedPlan.id ? updatedPlan : item))
      )
      setSaveMessage('Saved plan title updated.')
      handleCancelRenameSavedPlan()
    } catch (error) {
      setSavedPlansError(error instanceof Error ? error.message : 'Could not rename plan.')
    } finally {
      setIsSavingPlanTitle(false)
    }
  }

  function toggleSavedPlanExpanded(planId) {
    setExpandedSavedPlans((current) => ({
      ...current,
      [planId]: !current[planId],
    }))
  }

  function getSessionEditKey(day) {
    return `required:${day}`
  }

  function mapSavedPlanToApiPlan(plan) {
    return {
      summary: plan.summary,
      athlete_snapshot: plan.athleteSnapshot ?? [],
      coaching_notes: plan.coachingNotes ?? [],
      days: Array.isArray(plan.days) ? plan.days.map((day) => normalizeSavedPlanDay(day)) : [],
    }
  }

  function handleStartEditPlan(plan) {
    setPlanBeingEdited(plan)
    setEditInstructions('')
    setSelectedEditSessions({})
    setSelectedEditExercises({})
    setEditedPlanDraft(null)
    setEditPlanError('')
    setEditPlanMessage('')
    setActivePage('edit')
  }

  function resetEditWorkspace() {
    setPlanBeingEdited(null)
    setEditInstructions('')
    setSelectedEditSessions({})
    setSelectedEditExercises({})
    setEditedPlanDraft(null)
    setEditPlanError('')
    setEditPlanMessage('')
  }

  function toggleEditSession(day, focus = '') {
    const key = getSessionEditKey(day)
    setSelectedEditSessions((current) =>
      current[key] ? {} : { [key]: { selection_type: 'day', day, focus, exercise_name: '' } }
    )
    setSelectedEditExercises({})
  }

  function toggleEditExercise(day, exerciseName, focus = '') {
    const key = getSessionEditKey(day)
    setSelectedEditExercises((current) => {
      const currentItems = current[key] ?? []
      const isSameExerciseSelected =
        Object.keys(current).length === 1 && currentItems.includes(exerciseName)

      setSelectedEditSessions(
        isSameExerciseSelected
          ? {}
          : {
              [key]: {
                selection_type: 'exercise',
                day,
                focus,
                exercise_name: exerciseName,
              },
            }
      )

      if (isSameExerciseSelected) {
        return {}
      }

      return { [key]: [exerciseName] }
    })
  }

  async function handleSubmitPlanEdit(event) {
    event.preventDefault()

    if (!planBeingEdited) {
      return
    }

    setIsSubmittingEdit(true)
    setEditPlanError('')
    setEditPlanMessage('')

    try {
      const selectedSessionsPayload = Object.entries(selectedEditSessions).map(
        ([, selection]) => ({
          ...selection,
        })
      )

      const response = await fetch('/api/plan/edit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          intake: normalizeSavedPlanIntake(
            planBeingEdited.intake,
            Array.isArray(planBeingEdited.days)
              ? planBeingEdited.days.map((day) => day.day).filter(Boolean)
              : []
          ),
          original_plan: mapSavedPlanToApiPlan(planBeingEdited),
          edit_instructions: editInstructions,
          selected_sessions: selectedSessionsPayload,
          preserve_unselected: true,
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        const detail =
          typeof data?.detail === 'string'
            ? data.detail
            : data?.error || 'Plan edit failed.'
        throw new Error(detail)
      }

      setEditedPlanDraft(data)
      setGeneratedPlan(data)
      setEditPlanMessage('Updated plan generated. Review it below, then save changes.')
    } catch (error) {
      setEditPlanError(error instanceof Error ? error.message : 'Could not edit plan.')
    } finally {
      setIsSubmittingEdit(false)
    }
  }

  async function handleSaveEditedPlan() {
    if (!planBeingEdited || !editedPlanDraft) {
      return
    }

    setIsSavingEditedPlan(true)
    setEditPlanError('')

    try {
      let savedPlanResult = null

      try {
        savedPlanResult = await updateSavedPlan(
          userId,
          planBeingEdited.id,
          editedPlanDraft,
          planBeingEdited.intake
        )
        setSavedPlans((currentPlans) =>
          currentPlans.map((plan) => (plan.id === savedPlanResult.id ? savedPlanResult : plan))
        )
        setEditPlanMessage('Changes saved to your plan library.')
      } catch (updateError) {
        const replacementPlan = await createSavedPlan(
          userId,
          editedPlanDraft,
          planBeingEdited.intake
        )

        try {
          await deleteSavedPlan(userId, planBeingEdited.id)
        } catch {
          // Keep the new saved plan even if cleanup of the old row fails.
        }

        savedPlanResult = replacementPlan
        setSavedPlans((currentPlans) => {
          const withoutOriginal = currentPlans.filter((plan) => plan.id !== planBeingEdited.id)
          return [replacementPlan, ...withoutOriginal]
        })
        setEditPlanMessage(
          updateError instanceof Error
            ? 'Changes saved as a replacement plan because direct update was unavailable.'
            : 'Changes saved as a replacement plan.'
        )
      }

      setPlanBeingEdited(savedPlanResult)
      setSavedPlansError('')
      setSaveMessage('Saved plan updated.')
      setActivePage('saved')
    } catch (error) {
      setEditPlanError(error instanceof Error ? error.message : 'Could not save changes.')
    } finally {
      setIsSavingEditedPlan(false)
    }
  }

  function toggleSavedPlanDayExpanded(planId, dayKey) {
    const stateKey = `${planId}-${dayKey}`
    setExpandedSavedPlanDays((current) => ({
      ...current,
      [stateKey]: !current[stateKey],
    }))
  }

  function renderExerciseDetails(exercise) {
    const hasExtraDetails =
      (exercise.secondary_muscles && exercise.secondary_muscles.length > 0) ||
      exercise.movement_pattern ||
      (exercise.coaching_cues && exercise.coaching_cues.length > 0)

    if (!hasExtraDetails) {
      return null
    }

    return (
      <details className="mt-2 rounded-xl border border-white/8 bg-white/[0.02] px-3 py-2 text-sm">
        <summary className="cursor-pointer list-none font-medium text-[#ffcfad]">
          More details
        </summary>
        <div className="mt-2 space-y-1 text-[#cfc5b7]">
          {exercise.secondary_muscles?.length ? (
            <p>Also targets: {exercise.secondary_muscles.join(', ')}</p>
          ) : null}
          {exercise.movement_pattern ? (
            <p>Movement pattern: {exercise.movement_pattern}</p>
          ) : null}
          {exercise.coaching_cues?.length ? (
            <p>Coaching cues: {exercise.coaching_cues.join(' ')}</p>
          ) : null}
        </div>
      </details>
    )
  }

  function renderPlanPreview(plan, title, emptyText) {
    if (!plan) {
      return (
        <article className={`${cardClass} p-5`}>
          <p className={sectionLabelClass}>{title}</p>
          <p className="mt-3 text-sm leading-6 text-[#efe7d8]">{emptyText}</p>
        </article>
      )
    }

    return (
      <article className={`${cardClass} p-5`}>
        <p className={sectionLabelClass}>{title}</p>
        <h3 className="mt-2 text-xl font-semibold text-[#f9f2e8]">{plan.summary}</h3>
        <div className="mt-4 grid gap-3">
          {(plan.days ?? []).map((day) => (
            <div key={`${title}-${day.day}-${day.focus}`} className="rounded-2xl border border-white/8 bg-black/10 p-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className={sectionLabelClass}>{day.day}</p>
                  <p className="mt-1 font-medium text-[#f8f2e8]">{day.focus}</p>
                </div>
                <p className="text-sm text-[#cfc5b7]">{day.duration_minutes} min</p>
              </div>
              <div className="mt-3 space-y-2 text-sm leading-6 text-[#efe7d8]">
                {day.exercises?.map((exercise) => (
                  <div key={`${title}-${day.day}-${exercise.name}`} className="rounded-xl border border-white/8 bg-white/[0.02] px-3 py-2">
                    <p className="font-medium text-[#f8f2e8]">
                      {exercise.name} {exercise.sets}x{exercise.reps}
                    </p>
                    <p className="text-[#cfc5b7]">
                      {exercise.primary_muscle_group} · {exercise.equipment_used}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </article>
    )
  }

  function renderSidebar() {
    return (
      <aside className={`${panelClass} ${panelGlowClass} h-fit lg:sticky lg:top-4`}>
        <div>
          <p className={sectionLabelClass}>WorkoutAgent</p>
          <h1 className="mt-2 text-3xl leading-tight font-semibold tracking-[-0.04em] text-[#f9f2e8]">
            Training workspace
          </h1>
          <p className="mt-3 text-sm leading-6 text-[#efe7d8]">
            Move between planning, saved workouts, profile context, and backend quality
            signals without losing your place.
          </p>
        </div>

        <div className="mt-6 rounded-[24px] border border-white/10 bg-white/[0.03] p-4">
          <p className={sectionLabelClass}>Signed in</p>
          <p className="mt-2 text-sm text-[#efe7d8]">{userEmail}</p>
        </div>

        <nav className="mt-6 grid gap-2">
          {navItems.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => setActivePage(item.id)}
              className={`rounded-[18px] px-4 py-3 text-left text-sm font-medium transition ${
                activePage === item.id
                  ? 'bg-[linear-gradient(135deg,#f08f56,#da5d3d)] text-[#111]'
                  : 'border border-white/12 bg-white/[0.03] text-[#f5efe4] hover:-translate-y-0.5'
              }`}
            >
              {item.label}
            </button>
          ))}
        </nav>

        <div className="mt-6 grid gap-3">
          <div className={`${cardClass} p-4`}>
            <p className={sectionLabelClass}>Saved plans</p>
            <strong className="mt-2 block text-3xl text-[#f9f2e8]">{savedPlans.length}</strong>
          </div>
        </div>

        <button
          type="button"
          onClick={onSignOut}
          className="mt-6 rounded-full border border-white/12 bg-white/[0.03] px-4 py-3 text-sm font-medium text-[#f5efe4] transition hover:-translate-y-0.5 focus:outline-none focus:ring-2 focus:ring-[#f08f56]/30"
        >
          Sign out
        </button>
      </aside>
    )
  }

  function renderHomePage() {
    const latestSummary = generatedPlan?.summary ?? savedPlans[0]?.summary ?? 'No plan generated yet'

    return (
      <>
        <section className={`${panelClass} ${panelGlowClass}`}>
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => setActivePage('generate')}
              className="rounded-full bg-[linear-gradient(135deg,#f08f56,#da5d3d)] px-5 py-3 font-semibold text-[#111] transition hover:-translate-y-0.5"
            >
              Generate a plan
            </button>
            <button
              type="button"
              onClick={() => setActivePage('saved')}
              className="rounded-full border border-white/12 bg-white/[0.03] px-5 py-3 font-semibold text-[#f5efe4] transition hover:-translate-y-0.5"
            >
              Review saved plans
            </button>
          </div>

          <div className="mt-6 grid gap-3 md:grid-cols-3">
            <div className={`${cardClass} p-4`}>
              <p className={sectionLabelClass}>Latest summary</p>
              <p className="mt-2 text-sm leading-6 text-[#efe7d8]">{latestSummary}</p>
            </div>
            <div className={`${cardClass} p-4`}>
              <p className={sectionLabelClass}>Saved plan count</p>
              <strong className="mt-2 block text-3xl text-[#f9f2e8]">{savedPlans.length}</strong>
            </div>
            <div className={`${cardClass} p-4`}>
              <p className={sectionLabelClass}>Planner status</p>
              <p className="mt-2 text-sm leading-6 text-[#efe7d8]">
                {generatedPlan ? 'Plan ready to review' : 'Ready for first generation'}
              </p>
            </div>
          </div>
        </section>

        <section className="mt-6 grid gap-4">
          {[
            {
              title: 'AI Planner',
              text: 'Generate a personalized workout plan from your current profile and constraints.',
              target: 'generate',
            },
            {
              title: 'Saved Plans',
              text: 'Review the plans saved to your account.',
              target: 'saved',
            },
          ].map((item) => (
            <button
              key={item.title}
              type="button"
              onClick={() => setActivePage(item.target)}
              className={`${panelClass} ${panelGlowClass} text-left transition hover:-translate-y-1`}
            >
              <p className={sectionLabelClass}>{item.title}</p>
              <p className="mt-2 text-base leading-7 text-[#efe7d8]">{item.text}</p>
            </button>
          ))}
        </section>
      </>
    )
  }

  function renderGeneratePage() {
    return (
      <>
        <section className="grid gap-6">
          <form className={`${panelClass} ${panelGlowClass}`} onSubmit={handleSubmit}>
            <div className="mb-6 flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
              <div>
                <p className={sectionLabelClass}>Athlete intake</p>
                <h2 className="mt-2 text-[1.6rem] leading-tight font-semibold tracking-[-0.03em] text-[#f9f2e8]">
                  Generate a workout plan
                </h2>
              </div>
              <button
                className="w-fit rounded-full bg-[linear-gradient(135deg,#f08f56,#da5d3d)] px-4 py-3 font-semibold text-[#111] transition hover:-translate-y-0.5 focus:outline-none focus:ring-2 focus:ring-[#f08f56]/40 disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0"
                type="submit"
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Generating...' : 'Generate plan'}
              </button>
            </div>

            <div className="grid gap-6">
              <section className="grid gap-3">
                <div>
                  <p className={sectionLabelClass}>Planning preferences</p>
                  <h3 className="mt-2 text-lg font-semibold text-[#f9f2e8]">
                    Training experience and effort
                  </h3>
                </div>

                <div className="grid gap-[18px] md:grid-cols-2">
                  <div className="grid gap-3">
                    <label className={sectionLabelClass} htmlFor="experience">
                      Experience
                    </label>
                    <select
                      id="experience"
                      className={inputClass}
                      value={experience}
                      onChange={(event) => setExperience(event.target.value)}
                    >
                      {experienceLevels.map((item) => (
                        <option key={item} value={item}>
                          {item}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="grid gap-3">
                    <label className={sectionLabelClass} htmlFor="intensity-preference">
                      Intensity preference
                    </label>
                    <select
                      id="intensity-preference"
                      className={inputClass}
                      value={intensityPreference}
                      onChange={(event) => setIntensityPreference(event.target.value)}
                    >
                      {intensityPreferences.map((item) => (
                        <option key={item} value={item}>
                          {item}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </section>

              <section className="grid gap-3">
                <div>
                  <p className={sectionLabelClass}>Profile</p>
                  <h3 className="mt-2 text-lg font-semibold text-[#f9f2e8]">
                    Athlete baseline
                  </h3>
                </div>

                <div className="grid gap-[18px] md:grid-cols-2">
                  <div className="grid gap-3">
                    <label className={sectionLabelClass} htmlFor="age-range">
                      Age range
                    </label>
                    <select
                      id="age-range"
                      className={inputClass}
                      value={ageRange}
                      onChange={(event) => setAgeRange(event.target.value)}
                    >
                      {ageRanges.map((item) => (
                        <option key={item} value={item}>
                          {item}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="grid gap-3">
                    <label className={sectionLabelClass} htmlFor="activity-level">
                      Current activity level
                    </label>
                    <select
                      id="activity-level"
                      className={inputClass}
                      value={activityLevel}
                      onChange={(event) => setActivityLevel(event.target.value)}
                    >
                      {activityLevels.map((item) => (
                        <option key={item} value={item}>
                          {item}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </section>

              <section className="grid gap-3">
                <div>
                  <p className={sectionLabelClass}>Schedule</p>
                </div>

                <div className="grid gap-[18px] md:grid-cols-2">
                  <div className="grid gap-3">
                    <label className={sectionLabelClass}>Training days</label>
                    <div className={`${cardClass} px-4 py-3`}>
                      <span className="text-sm text-[#ffcfad]">{daysPerWeek} days/week selected</span>
                    </div>
                  </div>

                  <div className="grid gap-3">
                    <label className={sectionLabelClass}>Session length max</label>
                    <div className="grid gap-3">
                      <div className="flex items-center justify-between gap-3">
                        <span className="text-sm text-[#cfc5b7]">Max session time</span>
                        <span className="text-sm text-[#ffcfad]">{sessionLengthMax} min</span>
                      </div>
                      <input
                        className="w-full accent-[#f08f56]"
                        type="range"
                        min="20"
                        max="90"
                        step="5"
                        value={sessionLengthMax}
                        onChange={(event) => setSessionLengthMax(Number(event.target.value))}
                      />
                    </div>
                  </div>
                </div>

                <div className="grid gap-3">
                  <label className={sectionLabelClass}>Available training days</label>
                  <div className="flex flex-wrap gap-2.5">
                    {weekDays.map((day) => {
                      const selected = trainingDays.includes(day)

                      return (
                        <button
                          key={day}
                          type="button"
                          className={`rounded-full border px-3.5 py-2.5 text-sm transition hover:-translate-y-0.5 focus:outline-none focus:ring-2 focus:ring-[#f08f56]/30 ${
                            selected
                              ? 'border-[#ffb37c]/50 bg-[#f08f56]/18 text-[#ffcfad]'
                              : 'border-white/12 bg-white/[0.03] text-[#f8f2e8]'
                          }`}
                          onClick={() => toggleTrainingDay(day)}
                        >
                          {day}
                        </button>
                      )
                    })}
                  </div>
                  <p className="m-0 text-sm leading-6 text-[#c2b7a6]">
                    At least two days are required.
                  </p>
                </div>

              </section>

              <section className="grid gap-3">
                <div>
                  <p className={sectionLabelClass}>Constraints</p>
                </div>

                <div className="grid gap-3">
                  <label className={sectionLabelClass}>Equipment available</label>
                  <div className="flex flex-wrap gap-2.5">
                    {equipmentOptions.map((item) => {
                      const selected = equipment.includes(item)

                      return (
                        <button
                          key={item}
                          type="button"
                          className={`rounded-full border px-3.5 py-2.5 text-sm transition hover:-translate-y-0.5 focus:outline-none focus:ring-2 focus:ring-[#f08f56]/30 ${
                            selected
                              ? 'border-[#ffb37c]/50 bg-[#f08f56]/18 text-[#ffcfad]'
                              : 'border-white/12 bg-white/[0.03] text-[#f8f2e8]'
                          }`}
                          onClick={() => toggleEquipment(item)}
                        >
                          {item}
                        </button>
                      )
                    })}
                  </div>
                </div>

                <div className="grid gap-3">
                  <label className={sectionLabelClass} htmlFor="injuries">
                    Injuries or pain points
                  </label>
                  <textarea
                    id="injuries"
                    rows="3"
                    className={`${inputClass} min-h-24 resize-y`}
                    value={injuries}
                    onChange={(event) => setInjuries(event.target.value)}
                  />
                </div>

                <div className="grid gap-3">
                  <label className={sectionLabelClass} htmlFor="notes">
                    Context for the agent
                  </label>
                  <textarea
                    id="notes"
                    rows="4"
                    className={`${inputClass} min-h-28 resize-y`}
                    value={notes}
                    onChange={(event) => setNotes(event.target.value)}
                  />
                  <p className="m-0 text-sm leading-6 text-[#c2b7a6]">
                    Add schedule constraints, disliked movements, motivation issues, or
                    anything else that should shape the plan.
                  </p>
                </div>

                {submitError ? (
                  <div className="rounded-[18px] border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
                    {submitError}
                  </div>
                ) : null}
              </section>
            </div>
          </form>

          <section className={`${panelClass} ${panelGlowClass}`}>
            <div className="mb-6 flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
              <div>
                <p className={sectionLabelClass}>Plan</p>
                <h2 className="mt-2 text-[1.6rem] leading-tight font-semibold tracking-[-0.03em] text-[#f9f2e8]">
                  {generatedPlan
                    ? 'Live response from the API'
                    : 'Generate a plan to see the model output'}
                </h2>
              </div>
              <div className="flex flex-wrap gap-2">
                <div className="w-fit rounded-full border border-[#5b9575]/35 bg-[#5b9575]/16 px-3 py-2 text-sm text-[#c2b7a6]">
                  {generatedPlan ? 'API connected' : 'No output yet'}
                </div>
                {generatedPlan ? (
                  <button
                    type="button"
                    onClick={handleSavePlan}
                    className="rounded-full border border-white/12 bg-white/[0.03] px-3 py-2 text-sm text-[#f5efe4] transition hover:-translate-y-0.5"
                  >
                    Save plan
                  </button>
                ) : null}
              </div>
            </div>

            {saveMessage ? (
              <div className="mb-5 rounded-[18px] border border-emerald-400/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-100">
                {saveMessage}
              </div>
            ) : null}

            <article className={`${cardClass} p-5`}>
              <div>
                <p className={sectionLabelClass}>Current recommendation</p>
                <h3 className="mt-2 text-[1.8rem] leading-tight font-semibold tracking-[-0.04em]">
                  {generatedPlan
                    ? generatedPlan.summary
                    : `${daysPerWeek}-day plan for a ${experience.toLowerCase()} trainee`}
                </h3>
              </div>
              {generatedPlan ? (
                <ul className="mt-4 grid gap-2 text-sm leading-6 text-[#efe7d8]">
                  {generatedPlan.athlete_snapshot.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              ) : null}
            </article>

            {generatedPlan ? (
              <div className="mt-[22px] grid gap-3.5 md:grid-cols-2">
                {generatedPlan.days.map((session) => (
                  <article
                    key={session.day}
                    className={`${cardClass} min-h-[170px] space-y-3 p-[18px]`}
                  >
                    <p className={sectionLabelClass}>{session.day}</p>
                    <h3 className="text-[1.2rem] leading-tight font-semibold">
                      {session.focus}
                    </h3>
                    <p className="text-sm leading-6 text-[#efe7d8]">
                      {session.duration_minutes} minutes
                    </p>
                    <div className="text-sm leading-6 text-[#efe7d8]">
                      <p className="font-medium text-[#ffcfad]">Warmup</p>
                      <p>{session.warmup.join(', ')}</p>
                    </div>
                    <div className="text-sm leading-6 text-[#efe7d8]">
                      <p className="font-medium text-[#ffcfad]">Main work</p>
                      <div className="space-y-3">
                        {session.exercises.map((exercise) => (
                          <div
                            key={`${session.day}-${exercise.name}`}
                            className="rounded-2xl border border-white/8 bg-black/10 px-3 py-2.5"
                          >
                            <p className="font-medium text-[#f8f2e8]">
                              {exercise.name} {exercise.sets}x{exercise.reps}
                            </p>
                            <p className="text-[#cfc5b7]">
                              {exercise.primary_muscle_group} · {exercise.equipment_used} ·{' '}
                              {exercise.rest_seconds}s rest
                            </p>
                            {exercise.exercise_explanation ? (
                              <p className="text-[#efe7d8]">
                                Why: {exercise.exercise_explanation}
                              </p>
                            ) : null}
                            {renderExerciseDetails(exercise)}
                            <p className="text-[#cfc5b7]">{exercise.intensity_note}</p>
                            <p className="text-[#cfc5b7]">
                              Swap option: {exercise.substitution_note}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            ) : null}

            {generatedPlan ? (
              <div className="mt-[22px] grid gap-3.5 md:grid-cols-2">
                {generatedPlan.coaching_notes.slice(0, 4).map((note) => (
                  <article key={note} className={`${cardClass} grid gap-2 p-[18px]`}>
                    <p className={sectionLabelClass}>Coach note</p>
                    <span className="leading-6 text-[#efe7d8]">{note}</span>
                  </article>
                ))}
              </div>
            ) : null}

            <article className={`${cardClass} mt-[22px] p-5`}>
              <p className={sectionLabelClass}>
                {generatedPlan ? 'API output details' : 'Limitations being interpreted'}
              </p>
              {generatedPlan ? (
                <div className="mt-3 space-y-3 text-sm leading-6 text-[#efe7d8]">
                  {generatedPlan.days[0] ? (
                    <>
                      <p>
                        <span className="font-medium text-[#ffcfad]">Cooldown:</span>{' '}
                        {generatedPlan.days[0].cooldown.join(', ')}
                      </p>
                      <p>
                        <span className="font-medium text-[#ffcfad]">Coach notes:</span>{' '}
                        {generatedPlan.days[0].coach_notes.join(' ')}
                      </p>
                    </>
                  ) : null}
                </div>
              ) : (
                <p className="mt-3 m-0 leading-6 text-[#efe7d8]">
                  {injuries || 'No injuries added yet.'}
                </p>
              )}
            </article>
          </section>
        </section>
      </>
    )
  }

  function renderSavedPlansPage() {
    return (
      <section className="grid gap-4">
        <article className={`${panelClass} ${panelGlowClass}`}>
          <p className={sectionLabelClass}>Saved plans</p>
          <p className="mt-3 text-base leading-7 text-[#efe7d8]">
            Review, rename, edit, or delete the plans you want to keep around.
          </p>
        </article>

        <section className="grid gap-4">
          {savedPlansError ? (
            <article className={`${panelClass} ${panelGlowClass}`}>
              <p className={sectionLabelClass}>Storage error</p>
              <p className="mt-3 text-base leading-7 text-[#efe7d8]">{savedPlansError}</p>
            </article>
          ) : isLoadingSavedPlans ? (
            <article className={`${panelClass} ${panelGlowClass}`}>
              <p className={sectionLabelClass}>Loading saved plans</p>
              <p className="mt-3 text-base leading-7 text-[#efe7d8]">
                Pulling your saved plans from Supabase.
              </p>
            </article>
          ) : savedPlans.length === 0 ? (
            <article className={`${panelClass} ${panelGlowClass}`}>
              <p className={sectionLabelClass}>Nothing saved yet</p>
              <p className="mt-3 text-base leading-7 text-[#efe7d8]">
                Generate a plan on the AI Planner page, then click `Save plan` to keep
                it here for review.
              </p>
            </article>
          ) : (
            savedPlans.map((plan) => {
              const isExpanded = Boolean(expandedSavedPlans[plan.id])

              return (
                <article key={plan.id} className={`${panelClass} ${panelGlowClass}`}>
                  <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                    <div className="flex flex-1 items-start justify-between gap-4">
                      <div>
                        <p className={sectionLabelClass}>
                          Saved {new Date(plan.savedAt).toLocaleString()}
                        </p>
                        {renamingPlanId === plan.id ? (
                          <div className="mt-2 flex flex-wrap items-center gap-2">
                            <input
                              type="text"
                              value={renamingTitle}
                              onChange={(event) => setRenamingTitle(event.target.value)}
                              onClick={(event) => event.stopPropagation()}
                              className={`${inputClass} max-w-xl`}
                            />
                            <button
                              type="button"
                              onClick={(event) => {
                                event.stopPropagation()
                                void handleSaveSavedPlanTitle(plan)
                              }}
                              disabled={isSavingPlanTitle}
                              className="rounded-full border border-white/12 bg-white/[0.03] px-3 py-2 text-sm text-[#f5efe4] transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60"
                            >
                              {isSavingPlanTitle ? 'Saving...' : 'Save title'}
                            </button>
                            <button
                              type="button"
                              onClick={(event) => {
                                event.stopPropagation()
                                handleCancelRenameSavedPlan()
                              }}
                              className="rounded-full border border-white/12 bg-white/[0.03] px-3 py-2 text-sm text-[#f5efe4] transition hover:-translate-y-0.5"
                            >
                              Cancel
                            </button>
                          </div>
                        ) : (
                          <h3 className="mt-2 text-2xl leading-tight font-semibold tracking-[-0.03em] text-[#f9f2e8]">
                            {plan.summary}
                          </h3>
                        )}
                        <p className="mt-3 text-sm leading-6 text-[#cfc5b7]">
                          {plan.days.length} main day{plan.days.length === 1 ? '' : 's'}
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => toggleSavedPlanExpanded(plan.id)}
                        className="mt-1 inline-flex h-10 w-10 items-center justify-center rounded-full border border-white/10 bg-white/[0.03] text-xl text-[#f5efe4] transition hover:bg-white/[0.06]"
                      >
                        {isExpanded ? '⌄' : '›'}
                      </button>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <button
                        type="button"
                        onClick={() => handleStartRenameSavedPlan(plan)}
                        className="rounded-full border border-white/12 bg-white/[0.03] px-4 py-2 text-sm text-[#f5efe4] transition hover:-translate-y-0.5"
                      >
                        Rename
                      </button>
                      <button
                        type="button"
                        onClick={() => handleStartEditPlan(plan)}
                        className="rounded-full border border-white/12 bg-white/[0.03] px-4 py-2 text-sm text-[#f5efe4] transition hover:-translate-y-0.5"
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDeleteSavedPlan(plan.id)}
                        className="rounded-full border border-white/12 bg-white/[0.03] px-4 py-2 text-sm text-[#f5efe4] transition hover:-translate-y-0.5"
                      >
                        Delete
                      </button>
                    </div>
                  </div>

                  {isExpanded ? (
                    <div className="mt-5 grid gap-3 lg:grid-cols-2">
                      {plan.days.map((day) => {
                        const dayStateKey = `${plan.id}-${day.day}`
                        const isDayExpanded = Boolean(expandedSavedPlanDays[dayStateKey])

                        return (
                          <article key={dayStateKey} className={`${cardClass} p-3.5`}>
                            <button
                              type="button"
                              onClick={() => toggleSavedPlanDayExpanded(plan.id, day.day)}
                              className="-m-1 flex w-full items-start justify-between gap-3 rounded-[18px] p-1 text-left transition hover:bg-white/[0.02]"
                            >
                              <div>
                                <p className={sectionLabelClass}>{day.day}</p>
                                <h4 className="mt-1 text-base font-semibold text-[#f9f2e8]">
                                  {day.focus}
                                </h4>
                                <p className="mt-1 text-sm leading-6 text-[#cfc5b7]">
                                  {day.duration_minutes} minutes · {day.exercises.length} exercises
                                </p>
                              </div>
                              <span className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-white/10 bg-white/[0.03] text-lg text-[#f5efe4]">
                                {isDayExpanded ? '⌄' : '›'}
                              </span>
                            </button>

                            {isDayExpanded ? (
                              <div className="mt-3 text-sm leading-6 text-[#efe7d8]">
                                <div>
                                  <p className="font-medium text-[#ffcfad]">Warmup</p>
                                  <p>{day.warmup.join(', ')}</p>
                                </div>
                                <div className="mt-3 space-y-2">
                                  {day.exercises.map((exercise) => (
                                    <div
                                      key={`${plan.id}-${day.day}-${exercise.name}`}
                                      className="rounded-xl border border-white/8 bg-black/10 px-3 py-2"
                                    >
                                      <p className="font-medium text-[#f8f2e8]">
                                        {exercise.name} {exercise.sets}x{exercise.reps}
                                      </p>
                                      <p className="text-[#cfc5b7]">
                                        {exercise.primary_muscle_group} · {exercise.equipment_used} ·{' '}
                                        {exercise.rest_seconds}s rest
                                      </p>
                                      {exercise.exercise_explanation ? (
                                        <p className="text-[#efe7d8]">
                                          Why: {exercise.exercise_explanation}
                                        </p>
                                      ) : null}
                                      {renderExerciseDetails(exercise)}
                                      <p className="text-[#cfc5b7]">{exercise.intensity_note}</p>
                                      <p className="text-[#cfc5b7]">
                                        Swap option: {exercise.substitution_note}
                                      </p>
                                    </div>
                                  ))}
                                </div>
                                <div className="mt-3">
                                  <p className="font-medium text-[#ffcfad]">Cooldown</p>
                                  <p>{day.cooldown.join(', ')}</p>
                                </div>
                                <div className="mt-3">
                                  <p className="font-medium text-[#ffcfad]">Coach notes</p>
                                  <p>{day.coach_notes.join(' ')}</p>
                                </div>
                              </div>
                            ) : null}
                          </article>
                        )
                      })}

                    </div>
                  ) : (
                    <div className="mt-5 rounded-[22px] border border-white/10 bg-white/[0.03] px-4 py-3 text-sm leading-6 text-[#cfc5b7]">
                      Click to expand and see every scheduled day, exercises, and cooldowns.
                    </div>
                  )}
                </article>
              )
            })
          )}
        </section>
      </section>
    )
  }

  function renderEditPage() {
    const selectedSessionCount = Object.keys(selectedEditSessions).length

    if (!planBeingEdited) {
      return (
        <section className="grid gap-4">
          <article className={`${panelClass} ${panelGlowClass}`}>
            <p className={sectionLabelClass}>Edit plan</p>
            <h2 className="mt-2 text-[1.6rem] leading-tight font-semibold tracking-[-0.03em] text-[#f9f2e8]">
              Choose a saved plan to revise
            </h2>
            <p className="mt-4 text-base leading-7 text-[#efe7d8]">
              Open the Saved Plans page and click `Edit` on any plan to target specific
              days, exercises, and feedback for the model.
            </p>
            <button
              type="button"
              onClick={() => setActivePage('saved')}
              className="mt-5 rounded-full bg-[linear-gradient(135deg,#f08f56,#da5d3d)] px-5 py-3 font-semibold text-[#111] transition hover:-translate-y-0.5"
            >
              Go to saved plans
            </button>
          </article>
        </section>
      )
    }

    return (
      <section className="grid gap-6">
        <form className={`${panelClass} ${panelGlowClass}`} onSubmit={handleSubmitPlanEdit}>
          <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
            <div>
              <p className={sectionLabelClass}>Edit workspace</p>
              <h2 className="mt-2 text-[1.6rem] leading-tight font-semibold tracking-[-0.03em] text-[#f9f2e8]">
                {planBeingEdited.summary}
              </h2>
              <p className="mt-3 text-sm leading-6 text-[#efe7d8]">
                Pick one day or one exercise to change, then explain what should be
                removed, replaced, simplified, or rewritten.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                type="submit"
                disabled={isSubmittingEdit}
                className="rounded-[16px] bg-[linear-gradient(135deg,#f08f56,#da5d3d)] px-4 py-2.5 text-sm font-semibold text-[#111] transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isSubmittingEdit ? 'Updating...' : 'Update Plan'}
              </button>
              <button
                type="button"
                onClick={resetEditWorkspace}
                className="rounded-full border border-white/12 bg-white/[0.03] px-4 py-3 text-sm text-[#f5efe4] transition hover:-translate-y-0.5"
              >
                Clear
              </button>
            </div>
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-3">
            <div className={`${cardClass} p-4`}>
              <p className={sectionLabelClass}>Target plan</p>
              <p className="mt-2 text-sm leading-6 text-[#efe7d8]">
                Saved {new Date(planBeingEdited.savedAt).toLocaleString()}
              </p>
            </div>
            <div className={`${cardClass} p-4`}>
              <p className={sectionLabelClass}>Selected target</p>
              <strong className="mt-2 block text-3xl text-[#f9f2e8]">{selectedSessionCount}</strong>
            </div>
            <div className={`${cardClass} p-4`}>
              <p className={sectionLabelClass}>Feedback mode</p>
              <p className="mt-2 text-sm leading-6 text-[#efe7d8]">
                Single-target edits keep the rest of the week unchanged unless you ask for a broader rewrite.
              </p>
            </div>
          </div>

          <div className="mt-6 grid gap-4">
            <article className={`${cardClass} p-4`}>
              <p className={sectionLabelClass}>Required sessions</p>
              <p className="mt-2 text-sm leading-6 text-[#c2b7a6]">
                Selecting a new day or exercise replaces the previous target.
              </p>
              <div className="mt-3 grid gap-3">
                {planBeingEdited.days.map((day) => {
                  const sessionKey = getSessionEditKey(day.day)
                  const isSelected = Boolean(selectedEditSessions[sessionKey])

                  return (
                    <div key={sessionKey} className="rounded-2xl border border-white/8 bg-black/10 p-4">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className={sectionLabelClass}>{day.day}</p>
                          <p className="mt-1 font-medium text-[#f8f2e8]">{day.focus}</p>
                        </div>
                        <button
                          type="button"
                          onClick={() => toggleEditSession(day.day, day.focus)}
                          className={`rounded-full px-3 py-2 text-sm transition ${
                            isSelected
                              ? 'bg-[#f08f56]/18 text-[#ffcfad]'
                              : 'border border-white/12 bg-white/[0.03] text-[#f5efe4]'
                          }`}
                        >
                          {isSelected ? 'Selected' : 'Select day'}
                        </button>
                      </div>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {day.exercises.map((exercise) => {
                          const selectedExercises = selectedEditExercises[sessionKey] ?? []
                          const isExerciseSelected = selectedExercises.includes(exercise.name)

                          return (
                            <button
                              key={`${sessionKey}-${exercise.name}`}
                              type="button"
                              onClick={() =>
                                toggleEditExercise(day.day, exercise.name, day.focus)
                              }
                              className={`rounded-full border px-3 py-2 text-sm transition ${
                                isExerciseSelected
                                  ? 'border-[#8ec9a6]/45 bg-[#5b9575]/16 text-[#d8f2df]'
                                  : 'border-white/12 bg-white/[0.03] text-[#f8f2e8]'
                              }`}
                            >
                              {exercise.name}
                            </button>
                          )
                        })}
                      </div>
                    </div>
                  )
                })}
              </div>
            </article>

            <article className={`${cardClass} p-4`}>
              <label className={sectionLabelClass} htmlFor="edit-instructions">
                Edit request
              </label>
              <textarea
                id="edit-instructions"
                rows="7"
                className={`${inputClass} mt-3 min-h-36 resize-y`}
                value={editInstructions}
                onChange={(event) => setEditInstructions(event.target.value)}
                placeholder="Example: On Tuesday only, add one biceps exercise without changing any other day."
                required
              />
              <p className="mt-3 text-sm leading-6 text-[#c2b7a6]">
                Good prompts here mention what to remove, what to keep, any pain or
                equipment issue, and whether you want a local edit or a broader rewrite.
              </p>
            </article>

            {editPlanError ? (
              <div className="rounded-[18px] border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
                {editPlanError}
              </div>
            ) : null}

            {editPlanMessage ? (
              <div className="rounded-[18px] border border-emerald-400/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-100">
                {editPlanMessage}
              </div>
            ) : null}
          </div>
        </form>

        {editedPlanDraft ? (
          <section className="grid gap-4">
            {renderPlanPreview(
              editedPlanDraft,
              'Updated draft',
              'Generate an updated plan to preview the revised output here.'
            )}

            <article className={`${panelClass} ${panelGlowClass}`}>
              <p className={sectionLabelClass}>Save changes</p>
              <p className="mt-3 text-sm leading-6 text-[#efe7d8]">
                This will overwrite the existing saved plan with the updated version.
              </p>
              <div className="mt-4 flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={handleSaveEditedPlan}
                  disabled={isSavingEditedPlan}
                  className="rounded-[16px] bg-[linear-gradient(135deg,#f08f56,#da5d3d)] px-5 py-3 text-sm font-semibold text-[#111] transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isSavingEditedPlan ? 'Saving...' : 'Save changes to plan'}
                </button>
                <button
                  type="button"
                  onClick={() => setActivePage('saved')}
                  className="rounded-full border border-white/12 bg-white/[0.03] px-5 py-3 text-sm text-[#f5efe4] transition hover:-translate-y-0.5"
                >
                  Back to saved plans
                </button>
              </div>
            </article>
          </section>
        ) : null}
      </section>
    )
  }

  function renderProfilePage() {
    return (
      <section className="grid gap-6">
        <article className={`${panelClass} ${panelGlowClass}`}>
          <p className={sectionLabelClass}>Profile</p>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            {profileStats.map((item) => (
              <div key={item.label} className={`${cardClass} p-4`}>
                <p className={sectionLabelClass}>{item.label}</p>
                <p className="mt-2 text-sm leading-6 text-[#efe7d8]">{item.value}</p>
              </div>
            ))}
          </div>
        </article>

        <section className={`${panelClass} ${panelGlowClass}`}>
          <p className={sectionLabelClass}>Account</p>
          <div className="mt-4 space-y-4">
            <div className={`${cardClass} p-4`}>
              <p className={sectionLabelClass}>Signed-in email</p>
              <p className="mt-2 text-sm leading-6 text-[#efe7d8]">{userEmail}</p>
            </div>
            <div className={`${cardClass} p-4`}>
              <p className={sectionLabelClass}>Available training days</p>
              <p className="mt-2 text-sm leading-6 text-[#efe7d8]">
                {selectedTrainingDays.join(', ')}
              </p>
            </div>
            <div className={`${cardClass} p-4`}>
              <p className={sectionLabelClass}>Injury considerations</p>
              <p className="mt-2 text-sm leading-6 text-[#efe7d8]">{injuries}</p>
            </div>
            <div className={`${cardClass} p-4`}>
              <p className={sectionLabelClass}>Planning preferences</p>
              <p className="mt-2 text-sm leading-6 text-[#efe7d8]">
                {intensityPreference}
              </p>
            </div>
          </div>
        </section>
      </section>
    )
  }

  function renderActivePage() {
    if (activePage === 'home') {
      return renderHomePage()
    }

    if (activePage === 'saved') {
      return renderSavedPlansPage()
    }

    if (activePage === 'edit') {
      return renderEditPage()
    }

    if (activePage === 'profile') {
      return renderProfilePage()
    }

    return renderGeneratePage()
  }

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,rgba(240,119,64,0.22),transparent_28%),radial-gradient(circle_at_85%_20%,rgba(91,149,117,0.18),transparent_22%),linear-gradient(160deg,#201714_0%,#0e1113_52%,#12181a_100%)] text-[#f5efe4]">
      <section className="grid min-h-screen gap-0 lg:grid-cols-[280px_minmax(0,1fr)]">
        {renderSidebar()}
        <div className="px-3 py-4 sm:px-5 lg:px-8 lg:py-6">{renderActivePage()}</div>
      </section>
    </main>
  )
}

export default PlannerDashboard
