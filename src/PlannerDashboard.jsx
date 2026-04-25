import { useEffect, useMemo, useState } from 'react'
import { createSavedPlan, deleteSavedPlan, fetchSavedPlans } from './lib/savedPlans.js'

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
const workoutLocations = ['Home', 'Apartment gym', 'Commercial gym', 'Outdoors']
const cardioPreferences = [
  'No cardio preference',
  'Enjoys cardio',
  'Low-impact only',
  'Prefer minimal cardio',
]
const intensityPreferences = ['Light', 'Moderate', 'Challenging']
const varietyPreferences = ['Keep it simple', 'Mix it up', 'No preference']
const weekDays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
const navItems = [
  { id: 'home', label: 'Home' },
  { id: 'generate', label: 'AI Planner' },
  { id: 'saved', label: 'Saved Plans' },
  { id: 'calendar', label: 'Calendar' },
  { id: 'progress', label: 'Progress' },
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

function PlannerDashboard({ userId, userEmail, onSignOut }) {
  const [activePage, setActivePage] = useState('home')
  const [experience, setExperience] = useState(experienceLevels[0])
  const [equipment, setEquipment] = useState(['Dumbbells', 'Bench'])
  const [ageRange, setAgeRange] = useState(ageRanges[1])
  const [activityLevel, setActivityLevel] = useState(activityLevels[1])
  const [workoutLocation, setWorkoutLocation] = useState(workoutLocations[0])
  const [cardioPreference, setCardioPreference] = useState(cardioPreferences[3])
  const [intensityPreference, setIntensityPreference] = useState(intensityPreferences[1])
  const [varietyPreference, setVarietyPreference] = useState(varietyPreferences[0])
  const [daysPerWeek, setDaysPerWeek] = useState(4)
  const [sessionLength, setSessionLength] = useState(45)
  const [heightFeet, setHeightFeet] = useState(5)
  const [heightInches, setHeightInches] = useState(10)
  const [weightLbs, setWeightLbs] = useState(170)
  const [trainingDays, setTrainingDays] = useState(['Monday', 'Wednesday', 'Friday', 'Saturday'])
  const [flexibleDays, setFlexibleDays] = useState(['Tuesday'])
  const [injuries, setInjuries] = useState('Mild shoulder tightness from long desk hours.')
  const [equipmentDetails, setEquipmentDetails] = useState(
    'Adjustable dumbbells up to 50 lb, flat bench, and a treadmill.'
  )
  const [notes, setNotes] = useState(
    'Prefers short weekday sessions and one longer weekend workout. Enjoys simple, repeatable plans.'
  )
  const [generatedPlan, setGeneratedPlan] = useState(null)
  const [savedPlans, setSavedPlans] = useState([])
  const [expandedSavedPlans, setExpandedSavedPlans] = useState({})
  const [expandedSavedPlanDays, setExpandedSavedPlanDays] = useState({})
  const [isLoadingSavedPlans, setIsLoadingSavedPlans] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState('')
  const [saveMessage, setSaveMessage] = useState('')
  const [savedPlansError, setSavedPlansError] = useState('')

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

  const selectedTrainingDays = useMemo(() => {
    return trainingDays.slice(0, daysPerWeek)
  }, [trainingDays, daysPerWeek])

  const payloadPreview = useMemo(
    () => ({
      experience,
      equipment,
      age_range: ageRange,
      height_feet: heightFeet,
      height_inches: heightInches,
      weight_lbs: weightLbs,
      days_per_week: daysPerWeek,
      session_length: sessionLength,
      available_training_days: selectedTrainingDays,
      flexible_training_days: flexibleDays.filter((day) => !selectedTrainingDays.includes(day)),
      injuries,
      current_activity_level: activityLevel,
      workout_location: workoutLocation,
      equipment_details: equipmentDetails,
      cardio_preference: cardioPreference,
      intensity_preference: intensityPreference,
      variety_preference: varietyPreference,
      notes,
    }),
    [
      activityLevel,
      ageRange,
      cardioPreference,
      daysPerWeek,
      equipment,
      equipmentDetails,
      experience,
      flexibleDays,
      heightFeet,
      heightInches,
      intensityPreference,
      injuries,
      notes,
      selectedTrainingDays,
      sessionLength,
      varietyPreference,
      weightLbs,
      workoutLocation,
    ]
  )

  const fallbackPreviewDays = useMemo(() => {
    let focusPool = [
      'Upper body push',
      'Lower body strength',
      'Back + arms',
      'Full-body balance',
      'Posterior chain',
      'Core + conditioning',
    ]
    if (intensityPreference === 'Light') {
      focusPool = [
        'Foundational full body',
        'Joint-friendly lower body',
        'Upper body support',
        'Movement quality',
        'Low-stress conditioning',
        'Recovery flow',
      ]
    } else if (intensityPreference === 'Challenging') {
      focusPool = [
        'Upper body strength',
        'Lower body strength',
        'Pull + posterior chain',
        'Full-body performance',
        'Accessory volume',
        'Core finisher',
      ]
    }
    if (cardioPreference === 'Enjoys cardio') {
      focusPool = [...focusPool.slice(0, 4), 'Conditioning support', 'Steady cardio + core']
    } else if (cardioPreference === 'Prefer minimal cardio') {
      focusPool = [...focusPool.slice(0, 5), 'Core + mobility']
    }
    const fallbackDays = weekDays.filter((day) => !trainingDays.includes(day))
    const orderedDays = [...trainingDays, ...fallbackDays].slice(0, daysPerWeek)

    return orderedDays.map((day, index) => ({
      day: day.slice(0, 3),
      focus: focusPool[index % focusPool.length],
      detail:
        intensityPreference === 'Light'
          ? 'Controlled pace, joint-friendly movement, and a short low-stress finisher'
          : `${sessionLength}-minute session tuned for ${experience.toLowerCase()} progress and ${activityLevel.toLowerCase()} recovery`,
    }))
  }, [activityLevel, cardioPreference, daysPerWeek, experience, intensityPreference, sessionLength, trainingDays])

  const fallbackOptionalDays = useMemo(() => {
    return flexibleDays
      .filter((day) => !selectedTrainingDays.includes(day))
      .slice(0, 2)
      .map((day) => ({
        day: day.slice(0, 3),
        focus: 'Optional mobility or accessory work',
        detail: 'Use this day for a short bonus session if time and energy line up.',
      }))
  }, [flexibleDays, selectedTrainingDays])

  const profileStats = [
    { label: 'Current setup', value: `${workoutLocation} · ${equipment.join(', ')}` },
    { label: 'Training rhythm', value: `${daysPerWeek} days · ${sessionLength} min` },
    { label: 'Baseline activity', value: activityLevel },
    { label: 'Planning preferences', value: `${intensityPreference} · ${varietyPreference}` },
  ]

  const calendarItemsByDay = useMemo(() => {
    const grouped = Object.fromEntries(weekDays.map((day) => [day, []]))

    for (const plan of savedPlans) {
      for (const day of plan.days ?? []) {
        grouped[day.day]?.push({
          planId: plan.id,
          savedAt: plan.savedAt,
          summary: plan.summary,
          focus: day.focus,
          durationMinutes: day.duration_minutes,
          optional: false,
        })
      }

      for (const day of plan.optionalDays ?? []) {
        grouped[day.day]?.push({
          planId: plan.id,
          savedAt: plan.savedAt,
          summary: plan.summary,
          focus: day.focus,
          durationMinutes: day.duration_minutes,
          optional: true,
        })
      }
    }

    for (const day of weekDays) {
      grouped[day].sort((left, right) => {
        if (left.optional !== right.optional) {
          return left.optional ? 1 : -1
        }

        return new Date(right.savedAt).getTime() - new Date(left.savedAt).getTime()
      })
    }

    return grouped
  }, [savedPlans])

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

      if (currentDays.length >= 6) {
        return currentDays
      }

      return [...currentDays, day]
    })
  }

  function toggleFlexibleDay(day) {
    setFlexibleDays((currentDays) => {
      if (currentDays.includes(day)) {
        return currentDays.filter((item) => item !== day)
      }

      if (currentDays.length >= 3) {
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

  function toggleSavedPlanExpanded(planId) {
    setExpandedSavedPlans((current) => ({
      ...current,
      [planId]: !current[planId],
    }))
  }

  function toggleSavedPlanDayExpanded(planId, dayKey) {
    const stateKey = `${planId}-${dayKey}`
    setExpandedSavedPlanDays((current) => ({
      ...current,
      [stateKey]: !current[stateKey],
    }))
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
          <div className={`${cardClass} p-4`}>
            <p className={sectionLabelClass}>Latest provider</p>
            <p className="mt-2 text-sm leading-6 text-[#efe7d8]">
              {generatedPlan?.metadata?.provider_used ?? 'No live generation yet'}
            </p>
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
              <p className={sectionLabelClass}>Retrieval mode</p>
              <p className="mt-2 text-sm leading-6 text-[#efe7d8]">
                {generatedPlan?.metadata?.retrieval_strategy ?? 'Ready for first generation'}
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
            {
              title: 'Calendar',
              text: 'See your saved workouts grouped by weekday, including optional sessions.',
              target: 'calendar',
            },
            {
              title: 'Progress',
              text: 'Check the latest backend and generation signals.',
              target: 'progress',
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
                    <label className={sectionLabelClass}>Height</label>
                    <div className="flex flex-wrap items-center gap-3">
                      <div className="flex items-center gap-2">
                        <input
                          aria-label="Height in feet"
                          className={`${inputClass} w-20 px-3 py-2.5 text-center`}
                          type="number"
                          min="3"
                          max="8"
                          value={heightFeet}
                          onChange={(event) => setHeightFeet(Number(event.target.value))}
                        />
                        <span className="text-sm text-[#cfc5b7]">ft</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <input
                          aria-label="Height in inches"
                          className={`${inputClass} w-20 px-3 py-2.5 text-center`}
                          type="number"
                          min="0"
                          max="11"
                          value={heightInches}
                          onChange={(event) => setHeightInches(Number(event.target.value))}
                        />
                        <span className="text-sm text-[#cfc5b7]">in</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="grid gap-[18px] md:grid-cols-2">
                  <div className="grid gap-3">
                    <label className={sectionLabelClass} htmlFor="weight-lbs">
                      Weight (lb)
                    </label>
                    <input
                      id="weight-lbs"
                      className={inputClass}
                      type="number"
                      min="50"
                      max="700"
                      value={weightLbs}
                      onChange={(event) => setWeightLbs(Number(event.target.value))}
                    />
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
                  <h3 className="mt-2 text-lg font-semibold text-[#f9f2e8]">
                    When can they actually train?
                  </h3>
                </div>

                <div className="grid gap-[18px] md:grid-cols-2">
                  <div className="grid gap-3">
                    <div className="flex items-center justify-between gap-3">
                      <label className={sectionLabelClass} htmlFor="days-per-week">
                        Training days
                      </label>
                      <span className="text-sm text-[#ffcfad]">{daysPerWeek} days/week</span>
                    </div>
                    <input
                      id="days-per-week"
                      className="w-full accent-[#f08f56]"
                      type="range"
                      min="2"
                      max="6"
                      value={daysPerWeek}
                      onChange={(event) => setDaysPerWeek(Number(event.target.value))}
                    />
                  </div>

                  <div className="grid gap-3">
                    <div className="flex items-center justify-between gap-3">
                      <label className={sectionLabelClass} htmlFor="session-length">
                        Session length
                      </label>
                      <span className="text-sm text-[#ffcfad]">{sessionLength} min</span>
                    </div>
                    <input
                      id="session-length"
                      className="w-full accent-[#f08f56]"
                      type="range"
                      min="20"
                      max="90"
                      step="5"
                      value={sessionLength}
                      onChange={(event) => setSessionLength(Number(event.target.value))}
                    />
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
                    Pick at least two days. The request uses the first {daysPerWeek}{' '}
                    selected days.
                  </p>
                </div>

                <div className="grid gap-3">
                  <label className={sectionLabelClass}>Flexible or bonus days</label>
                  <div className="flex flex-wrap gap-2.5">
                    {weekDays.map((day) => {
                      const selected = flexibleDays.includes(day)
                      const disabled = selectedTrainingDays.includes(day)

                      return (
                        <button
                          key={`flex-${day}`}
                          type="button"
                          disabled={disabled}
                          className={`rounded-full border px-3.5 py-2.5 text-sm transition focus:outline-none focus:ring-2 focus:ring-[#f08f56]/30 ${
                            disabled
                              ? 'cursor-not-allowed border-white/6 bg-white/[0.02] text-[#7e786e]'
                              : selected
                                ? 'border-[#8ec9a6]/45 bg-[#5b9575]/16 text-[#d8f2df] hover:-translate-y-0.5'
                                : 'border-white/12 bg-white/[0.03] text-[#f8f2e8] hover:-translate-y-0.5'
                          }`}
                          onClick={() => toggleFlexibleDay(day)}
                        >
                          {day}
                        </button>
                      )
                    })}
                  </div>
                  <p className="m-0 text-sm leading-6 text-[#c2b7a6]">
                    Optional days can be used for bonus mobility, cardio, or accessory work.
                  </p>
                </div>
              </section>

              <section className="grid gap-3">
                <div>
                  <p className={sectionLabelClass}>Constraints</p>
                  <h3 className="mt-2 text-lg font-semibold text-[#f9f2e8]">
                    Limitations, gear, and anything the model should avoid
                  </h3>
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
                  <p className="m-0 text-sm leading-6 text-[#c2b7a6]">
                    Pick every setup the user can realistically train with.
                  </p>
                </div>

                <div className="grid gap-[18px] md:grid-cols-2">
                  <div className="grid gap-3">
                    <label className={sectionLabelClass} htmlFor="workout-location">
                      Workout location
                    </label>
                    <select
                      id="workout-location"
                      className={inputClass}
                      value={workoutLocation}
                      onChange={(event) => setWorkoutLocation(event.target.value)}
                    >
                      {workoutLocations.map((item) => (
                        <option key={item} value={item}>
                          {item}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="grid gap-3">
                    <label className={sectionLabelClass} htmlFor="cardio-preference">
                      Cardio preference
                    </label>
                    <select
                      id="cardio-preference"
                      className={inputClass}
                      value={cardioPreference}
                      onChange={(event) => setCardioPreference(event.target.value)}
                    >
                      {cardioPreferences.map((item) => (
                        <option key={item} value={item}>
                          {item}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="grid gap-[18px] md:grid-cols-2">
                  <div className="grid gap-3">
                    <label className={sectionLabelClass} htmlFor="equipment-details">
                      Equipment details (optional)
                    </label>
                    <input
                      id="equipment-details"
                      className={inputClass}
                      value={equipmentDetails}
                      onChange={(event) => setEquipmentDetails(event.target.value)}
                      placeholder="Example: adjustable dumbbells up to 50 lb, flat bench, no squat rack"
                    />
                    <p className="m-0 text-sm leading-6 text-[#c2b7a6]">
                      Add specifics the checklist does not capture, like weight limits,
                      missing attachments, or one-off pieces of gear.
                    </p>
                  </div>

                  <div className="grid gap-[18px] md:grid-cols-2">
                    <div className="grid gap-3">
                      <label className={sectionLabelClass} htmlFor="variety-preference">
                        Variety preference
                      </label>
                      <select
                        id="variety-preference"
                        className={inputClass}
                        value={varietyPreference}
                        onChange={(event) => setVarietyPreference(event.target.value)}
                      >
                        {varietyPreferences.map((item) => (
                          <option key={item} value={item}>
                            {item}
                          </option>
                        ))}
                      </select>
                    </div>
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
                    : 'What the generated experience could feel like'}
                </h2>
              </div>
              <div className="flex flex-wrap gap-2">
                <div className="w-fit rounded-full border border-[#5b9575]/35 bg-[#5b9575]/16 px-3 py-2 text-sm text-[#c2b7a6]">
                  {generatedPlan ? 'API connected' : 'Preview only'}
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
              ) : (
                <p className="mt-4 m-0 leading-6 text-[#efe7d8]">
                  {ageRange}, {heightFeet} ft {heightInches} in, {weightLbs} lb, {activityLevel.toLowerCase()} and
                  training mostly at {workoutLocation.toLowerCase()}. Training on{' '}
                  {selectedTrainingDays.join(', ')} for roughly {sessionLength}-minute
                  sessions with a {intensityPreference.toLowerCase()} feel.
                  {fallbackOptionalDays.length
                    ? ` Optional bonus days: ${fallbackOptionalDays.map((day) => day.day).join(', ')}.`
                    : ''}
                </p>
              )}
            </article>

            <div className="mt-[22px] grid gap-3.5 md:grid-cols-2">
              {generatedPlan
                ? generatedPlan.days.map((session) => (
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
                              <p className="text-[#cfc5b7]">{exercise.intensity_note}</p>
                              <p className="text-[#cfc5b7]">
                                Swap option: {exercise.substitution_note}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    </article>
                  ))
                : fallbackPreviewDays.map((session) => (
                    <article
                      key={session.day}
                      className={`${cardClass} min-h-[170px] p-[18px]`}
                    >
                      <p className={sectionLabelClass}>{session.day}</p>
                      <h3 className="mt-2 mb-2.5 text-[1.2rem] leading-tight font-semibold">
                        {session.focus}
                      </h3>
                      <p className="m-0 leading-6 text-[#efe7d8]">{session.detail}</p>
                    </article>
                  ))}
            </div>

            {(generatedPlan?.optional_days?.length || fallbackOptionalDays.length) ? (
              <div className="mt-[22px] grid gap-3.5">
                <p className={sectionLabelClass}>Optional sessions</p>
                {(generatedPlan?.optional_days?.length
                  ? generatedPlan.optional_days
                  : fallbackOptionalDays
                ).map((session) =>
                  generatedPlan?.optional_days?.length ? (
                    <article
                      key={`optional-${session.day}`}
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
                        <p className="font-medium text-[#8ec9a6]">Main work</p>
                        <p>
                          {session.exercises
                            .map((exercise) => `${exercise.name} ${exercise.sets}x${exercise.reps}`)
                            .join(', ')}
                        </p>
                      </div>
                      <p className="text-sm leading-6 text-[#cfc5b7]">
                        {session.coach_notes.join(' ')}
                      </p>
                    </article>
                  ) : (
                    <article
                      key={`optional-${session.day}`}
                      className={`${cardClass} min-h-[140px] p-[18px]`}
                    >
                      <p className={sectionLabelClass}>{session.day}</p>
                      <h3 className="mt-2 mb-2.5 text-[1.1rem] leading-tight font-semibold">
                        {session.focus}
                      </h3>
                      <p className="m-0 leading-6 text-[#efe7d8]">{session.detail}</p>
                    </article>
                  )
                )}
              </div>
            ) : null}

            <div className="mt-[22px] grid gap-3.5 md:grid-cols-2">
              {generatedPlan ? (
                generatedPlan.coaching_notes.slice(0, 4).map((note) => (
                  <article key={note} className={`${cardClass} grid gap-2 p-[18px]`}>
                    <p className={sectionLabelClass}>Coach note</p>
                    <span className="leading-6 text-[#efe7d8]">{note}</span>
                  </article>
                ))
              ) : (
                <>
                  <article className={`${cardClass} grid gap-2 p-[18px]`}>
                    <p className={sectionLabelClass}>Plan preference</p>
                    <strong className="text-[1.05rem]">
                      {intensityPreference} intensity + {varietyPreference}
                    </strong>
                    <span className="leading-6 text-[#efe7d8]">
                      The plan should match how hard the user wants to work and how
                      much novelty they want week to week.
                    </span>
                  </article>
                  <article className={`${cardClass} grid gap-2 p-[18px]`}>
                    <p className={sectionLabelClass}>Constraint check</p>
                    <strong className="text-[1.05rem]">
                      {workoutLocation} · {equipment.join(', ')}
                    </strong>
                    <span className="leading-6 text-[#efe7d8]">
                      The model should use the actual setup: {equipmentDetails}
                    </span>
                  </article>
                </>
              )}
            </div>

            {generatedPlan?.metadata ? (
              <article className={`${cardClass} mt-[22px] p-5`}>
                <p className={sectionLabelClass}>Response metadata</p>
                <div className="mt-3 grid gap-2 text-sm leading-6 text-[#efe7d8] md:grid-cols-2">
                  <p>
                    <span className="font-medium text-[#ffcfad]">Requested:</span>{' '}
                    {generatedPlan.metadata.provider_requested}
                  </p>
                  <p>
                    <span className="font-medium text-[#ffcfad]">Used:</span>{' '}
                    {generatedPlan.metadata.provider_used}
                  </p>
                  <p>
                    <span className="font-medium text-[#ffcfad]">Model:</span>{' '}
                    {generatedPlan.metadata.model_used}
                  </p>
                  <p>
                    <span className="font-medium text-[#ffcfad]">Candidates:</span>{' '}
                    {generatedPlan.metadata.candidate_exercise_count}
                  </p>
                  <p>
                    <span className="font-medium text-[#ffcfad]">Retrieved chunks:</span>{' '}
                    {generatedPlan.metadata.retrieved_chunk_count}
                  </p>
                  <p>
                    <span className="font-medium text-[#ffcfad]">Fallback:</span>{' '}
                    {generatedPlan.metadata.fallback_used ? 'Yes' : 'No'}
                  </p>
                  <p>
                    <span className="font-medium text-[#ffcfad]">Retrieval:</span>{' '}
                    {generatedPlan.metadata.retrieval_strategy}
                  </p>
                  <p>
                    <span className="font-medium text-[#ffcfad]">Truncated:</span>{' '}
                    {generatedPlan.metadata.retrieval_truncated ? 'Yes' : 'No'}
                  </p>
                  <p>
                    <span className="font-medium text-[#ffcfad]">Generated:</span>{' '}
                    {generatedPlan.metadata.generated_at}
                  </p>
                </div>
                {generatedPlan.metadata.fallback_reason ? (
                  <p className="mt-3 text-sm leading-6 text-[#cfc5b7]">
                    <span className="font-medium text-[#ffcfad]">Fallback reason:</span>{' '}
                    {generatedPlan.metadata.fallback_reason}
                  </p>
                ) : null}
              </article>
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

            <article className={`${cardClass} mt-[22px] p-5`}>
              <p className={sectionLabelClass}>Submission payload preview</p>
              <pre className="mt-3 overflow-x-auto whitespace-pre-wrap text-sm leading-6 text-[#efe7d8]">
                {JSON.stringify(payloadPreview, null, 2)}
              </pre>
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
          <div className="mt-3 grid gap-3 md:grid-cols-2">
              <div className={`${cardClass} p-4`}>
                <p className={sectionLabelClass}>Saved count</p>
                <strong className="mt-2 block text-3xl text-[#f9f2e8]">{savedPlans.length}</strong>
              </div>
              <div className={`${cardClass} p-4`}>
                <p className={sectionLabelClass}>Storage</p>
                <p className="mt-2 text-sm leading-6 text-[#efe7d8]">
                  Supabase-backed plan library tied to the signed-in account.
                </p>
              </div>
            </div>
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
                    <button
                      type="button"
                      onClick={() => toggleSavedPlanExpanded(plan.id)}
                      className="-m-1 flex flex-1 items-start justify-between gap-4 rounded-[22px] p-1 text-left transition hover:bg-white/[0.02]"
                    >
                      <div>
                        <p className={sectionLabelClass}>
                          Saved {new Date(plan.savedAt).toLocaleString()}
                        </p>
                        <h3 className="mt-2 text-2xl leading-tight font-semibold tracking-[-0.03em] text-[#f9f2e8]">
                          {plan.summary}
                        </h3>
                        <p className="mt-3 text-sm leading-6 text-[#cfc5b7]">
                          {plan.days.length} main day{plan.days.length === 1 ? '' : 's'}
                          {plan.optionalDays?.length
                            ? ` · ${plan.optionalDays.length} optional session${
                                plan.optionalDays.length === 1 ? '' : 's'
                              }`
                            : ''}
                        </p>
                      </div>
                      <span className="mt-1 inline-flex h-10 w-10 items-center justify-center rounded-full border border-white/10 bg-white/[0.03] text-xl text-[#f5efe4]">
                        {isExpanded ? '⌄' : '›'}
                      </span>
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDeleteSavedPlan(plan.id)}
                      className="rounded-full border border-white/12 bg-white/[0.03] px-4 py-2 text-sm text-[#f5efe4] transition hover:-translate-y-0.5"
                    >
                      Delete
                    </button>
                  </div>

                  <div className="mt-5 grid gap-3 md:grid-cols-2">
                    <div className={`${cardClass} p-4`}>
                      <p className={sectionLabelClass}>Provider</p>
                      <p className="mt-2 text-sm leading-6 text-[#efe7d8]">
                        {plan.metadata.provider_used} · {plan.metadata.model_used}
                      </p>
                    </div>
                    <div className={`${cardClass} p-4`}>
                      <p className={sectionLabelClass}>Retrieved context</p>
                      <p className="mt-2 text-sm leading-6 text-[#efe7d8]">
                        {plan.metadata.candidate_exercise_count} candidates ·{' '}
                        {plan.metadata.retrieved_chunk_count} chunks
                      </p>
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

                      {plan.optionalDays?.length ? (
                        <article className={`${cardClass} p-3.5 lg:col-span-2`}>
                          <p className={sectionLabelClass}>Optional sessions</p>
                          <div className="mt-3 grid gap-3 lg:grid-cols-2">
                            {plan.optionalDays.map((day) => {
                              const optionalStateKey = `${plan.id}-optional-${day.day}`
                              const isOptionalExpanded = Boolean(
                                expandedSavedPlanDays[optionalStateKey]
                              )

                              return (
                                <div
                                  key={optionalStateKey}
                                  className="rounded-2xl border border-[#5b9575]/20 bg-[#5b9575]/8 p-3.5"
                                >
                                  <button
                                    type="button"
                                    onClick={() =>
                                      toggleSavedPlanDayExpanded(plan.id, `optional-${day.day}`)
                                    }
                                    className="-m-1 flex w-full items-start justify-between gap-3 rounded-[18px] p-1 text-left transition hover:bg-white/[0.02]"
                                  >
                                    <div>
                                      <p className={sectionLabelClass}>{day.day}</p>
                                      <h4 className="mt-1 text-base font-semibold text-[#d8f2df]">
                                        {day.focus}
                                      </h4>
                                      <p className="mt-1 text-sm leading-6 text-[#efe7d8]">
                                        {day.duration_minutes} minutes · {day.exercises.length}{' '}
                                        exercises
                                      </p>
                                    </div>
                                    <span className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-white/10 bg-white/[0.03] text-lg text-[#f5efe4]">
                                      {isOptionalExpanded ? '⌄' : '›'}
                                    </span>
                                  </button>

                                  {isOptionalExpanded ? (
                                    <div className="mt-3 text-sm leading-6 text-[#efe7d8]">
                                      <p>
                                        {day.exercises
                                          .map(
                                            (exercise) =>
                                              `${exercise.name} ${exercise.sets}x${exercise.reps}`
                                          )
                                          .join(', ')}
                                      </p>
                                      <p className="mt-2 text-[#cfc5b7]">
                                        {day.coach_notes.join(' ')}
                                      </p>
                                    </div>
                                  ) : null}
                                </div>
                              )
                            })}
                          </div>
                        </article>
                      ) : null}
                    </div>
                  ) : (
                    <div className="mt-5 rounded-[22px] border border-white/10 bg-white/[0.03] px-4 py-3 text-sm leading-6 text-[#cfc5b7]">
                      Click to expand and see every scheduled day, exercises, cooldowns,
                      and optional sessions.
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

  function renderCalendarPage() {
    return (
      <section className="grid gap-4">
        <article className={`${panelClass} ${panelGlowClass}`}>
          <p className={sectionLabelClass}>Weekly calendar</p>
          <div className="mt-3 grid gap-3 md:grid-cols-3">
            <div className={`${cardClass} p-4`}>
              <p className={sectionLabelClass}>Saved plans</p>
              <strong className="mt-2 block text-3xl text-[#f9f2e8]">{savedPlans.length}</strong>
            </div>
            <div className={`${cardClass} p-4`}>
              <p className={sectionLabelClass}>Optional sessions</p>
              <strong className="mt-2 block text-3xl text-[#f9f2e8]">
                {savedPlans.reduce(
                  (total, plan) => total + (plan.optionalDays?.length ?? 0),
                  0
                )}
              </strong>
            </div>
            <div className={`${cardClass} p-4`}>
              <p className={sectionLabelClass}>View</p>
              <p className="mt-2 text-sm leading-6 text-[#efe7d8]">
                Sessions grouped by weekday from your saved plans.
              </p>
            </div>
          </div>
        </article>

        {savedPlansError ? (
          <article className={`${panelClass} ${panelGlowClass}`}>
            <p className={sectionLabelClass}>Storage error</p>
            <p className="mt-3 text-base leading-7 text-[#efe7d8]">{savedPlansError}</p>
          </article>
        ) : isLoadingSavedPlans ? (
          <article className={`${panelClass} ${panelGlowClass}`}>
            <p className={sectionLabelClass}>Loading calendar</p>
            <p className="mt-3 text-base leading-7 text-[#efe7d8]">
              Pulling saved plan sessions from Supabase.
            </p>
          </article>
        ) : (
          <section className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
            {weekDays.map((day) => (
              <article key={day} className={`${panelClass} ${panelGlowClass}`}>
                <p className={sectionLabelClass}>{day}</p>
                <div className="mt-4 grid gap-3">
                  {calendarItemsByDay[day].length ? (
                    calendarItemsByDay[day].map((item) => (
                      <div key={`${day}-${item.planId}-${item.focus}`} className={`${cardClass} p-4`}>
                        <div className="flex items-center justify-between gap-3">
                          <h3 className="text-base font-semibold text-[#f9f2e8]">{item.focus}</h3>
                          <span
                            className={`rounded-full px-2.5 py-1 text-[0.72rem] uppercase tracking-[0.14em] ${
                              item.optional
                                ? 'bg-[#5b9575]/16 text-[#d8f2df]'
                                : 'bg-[#f08f56]/16 text-[#ffcfad]'
                            }`}
                          >
                            {item.optional ? 'Bonus' : 'Main'}
                          </span>
                        </div>
                        <p className="mt-2 text-sm leading-6 text-[#efe7d8]">{item.summary}</p>
                        <p className="mt-2 text-sm leading-6 text-[#cfc5b7]">
                          {item.durationMinutes} minutes · saved{' '}
                          {new Date(item.savedAt).toLocaleDateString()}
                        </p>
                      </div>
                    ))
                  ) : (
                    <div className={`${cardClass} p-4`}>
                      <p className="text-sm leading-6 text-[#cfc5b7]">
                        No saved sessions scheduled for this day yet.
                      </p>
                    </div>
                  )}
                </div>
              </article>
            ))}
          </section>
        )}
      </section>
    )
  }

  function renderProgressPage() {
    const latestMetadata = generatedPlan?.metadata ?? savedPlans[0]?.metadata ?? null

    return (
      <section className="grid gap-6">
        <article className={`${panelClass} ${panelGlowClass}`}>
          <p className={sectionLabelClass}>Progress overview</p>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <div className={`${cardClass} p-4`}>
              <p className={sectionLabelClass}>Generated this session</p>
              <strong className="mt-2 block text-3xl text-[#f9f2e8]">
                {generatedPlan ? 1 : 0}
              </strong>
            </div>
            <div className={`${cardClass} p-4`}>
              <p className={sectionLabelClass}>Saved plan library</p>
              <strong className="mt-2 block text-3xl text-[#f9f2e8]">{savedPlans.length}</strong>
            </div>
          </div>
        </article>

        <section className={`${panelClass} ${panelGlowClass}`}>
          <p className={sectionLabelClass}>System snapshot</p>
          {latestMetadata ? (
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <div className={`${cardClass} p-4`}>
                <p className={sectionLabelClass}>Provider</p>
                <p className="mt-2 text-sm leading-6 text-[#efe7d8]">
                  {latestMetadata.provider_used}
                </p>
              </div>
              <div className={`${cardClass} p-4`}>
                <p className={sectionLabelClass}>Model</p>
                <p className="mt-2 text-sm leading-6 text-[#efe7d8]">{latestMetadata.model_used}</p>
              </div>
              <div className={`${cardClass} p-4`}>
                <p className={sectionLabelClass}>Retrieved chunks</p>
                <p className="mt-2 text-sm leading-6 text-[#efe7d8]">
                  {latestMetadata.retrieved_chunk_count}
                </p>
              </div>
              <div className={`${cardClass} p-4`}>
                <p className={sectionLabelClass}>Fallback used</p>
                <p className="mt-2 text-sm leading-6 text-[#efe7d8]">
                  {latestMetadata.fallback_used ? 'Yes' : 'No'}
                </p>
              </div>
            </div>
          ) : (
            <p className="mt-5 text-base leading-7 text-[#efe7d8]">
              Generate a plan first to start collecting useful backend quality signals.
            </p>
          )}
        </section>
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
              <p className={sectionLabelClass}>Flexible days</p>
              <p className="mt-2 text-sm leading-6 text-[#efe7d8]">
                {payloadPreview.flexible_training_days.length
                  ? payloadPreview.flexible_training_days.join(', ')
                  : 'None'}
              </p>
            </div>
            <div className={`${cardClass} p-4`}>
              <p className={sectionLabelClass}>Injury considerations</p>
              <p className="mt-2 text-sm leading-6 text-[#efe7d8]">{injuries}</p>
            </div>
            <div className={`${cardClass} p-4`}>
              <p className={sectionLabelClass}>Equipment details</p>
              <p className="mt-2 text-sm leading-6 text-[#efe7d8]">{equipmentDetails}</p>
            </div>
            <div className={`${cardClass} p-4`}>
              <p className={sectionLabelClass}>Planning preferences</p>
              <p className="mt-2 text-sm leading-6 text-[#efe7d8]">
                {cardioPreference} · {intensityPreference} · {varietyPreference}
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

    if (activePage === 'calendar') {
      return renderCalendarPage()
    }

    if (activePage === 'progress') {
      return renderProgressPage()
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
