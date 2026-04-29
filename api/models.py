from typing import Literal

from pydantic import BaseModel, Field

ExperienceType = Literal["Beginner", "Intermediate", "Advanced"]

EquipmentType = Literal[
    "Bodyweight",
    "Dumbbells",
    "Resistance bands",
    "Bench",
    "Barbell / rack",
    "Machines / cables",
    "Cardio equipment",
    "Kettlebells",
    "Pull-up bar",
    "Mat / floor space",
]

ActivityLevelType = Literal[
    "Mostly sedentary",
    "Lightly active",
    "Moderately active",
    "Very active",
]

IntensityPreferenceType = Literal["Light", "Moderate", "Challenging"]

AgeRangeType = Literal[
    "Under 18",
    "18-24",
    "25-34",
    "35-44",
    "45-54",
    "55+",
]

DayNameType = Literal[
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


class SessionResponse(BaseModel):
    session_id: str
    created_at: str


class PlanRequest(BaseModel):
    experience: ExperienceType
    equipment: list[EquipmentType] = Field(..., min_length=1, max_length=10)
    age_range: AgeRangeType
    days_per_week: int = Field(..., ge=2, le=7)
    session_length_min: int = Field(..., ge=20, le=90)
    session_length_max: int = Field(..., ge=20, le=90)
    available_training_days: list[DayNameType] = Field(..., min_length=2, max_length=7)
    injuries: str = ""
    current_activity_level: ActivityLevelType
    intensity_preference: IntensityPreferenceType
    notes: str = ""


class NormalizedAthleteProfile(BaseModel):
    experience: ExperienceType
    age_range: AgeRangeType
    current_activity_level: ActivityLevelType


class NormalizedConstraints(BaseModel):
    equipment: list[EquipmentType] = Field(..., min_length=1, max_length=10)
    days_per_week: int = Field(..., ge=2, le=7)
    session_length_min: int = Field(..., ge=20, le=90)
    session_length_max: int = Field(..., ge=20, le=90)
    available_training_days: list[DayNameType] = Field(..., min_length=2, max_length=7)
    injuries: str


class NormalizedPreferences(BaseModel):
    intensity_preference: IntensityPreferenceType
    notes: str


class NormalizedPlanRequest(BaseModel):
    athlete_profile: NormalizedAthleteProfile
    constraints: NormalizedConstraints
    preferences: NormalizedPreferences


class ExerciseCandidate(BaseModel):
    name: str = Field(..., min_length=1)
    primary_muscle_group: str = Field(..., min_length=1, max_length=80)
    secondary_muscles: list[str] = Field(default_factory=list, max_length=6)
    equipment_used: str = Field(..., min_length=1, max_length=80)
    movement_pattern: str = Field(..., min_length=1, max_length=80)
    coaching_cues: list[str] = Field(default_factory=list, max_length=4)
    contraindications: list[str] = Field(default_factory=list, max_length=5)


class RetrievedContextChunk(BaseModel):
    source_id: str
    title: str
    score: float = Field(..., ge=0)
    content: str = Field(..., min_length=1)
    movement_pattern: str = Field(..., min_length=1, max_length=80)
    equipment_used: str = Field(..., min_length=1, max_length=80)


class SplitTemplateDay(BaseModel):
    focus: str = Field(..., min_length=1, max_length=80)
    key_patterns: list[str] = Field(..., min_length=1, max_length=4)


class SplitTemplate(BaseModel):
    id: str = Field(..., min_length=1, max_length=80)
    label: str = Field(..., min_length=1, max_length=120)
    summary: str = Field(..., min_length=1, max_length=240)
    days_per_week: int = Field(..., ge=2, le=7)
    equipment_tags: list[EquipmentType] = Field(default_factory=list, max_length=10)
    day_blueprints: list[SplitTemplateDay] = Field(..., min_length=2, max_length=7)
    when_to_prefer: list[str] = Field(default_factory=list, max_length=4)
    when_to_avoid: list[str] = Field(default_factory=list, max_length=4)


class SplitTemplateMatch(BaseModel):
    template_id: str = Field(..., min_length=1, max_length=80)
    label: str = Field(..., min_length=1, max_length=120)
    score: float = Field(..., ge=0)
    summary: str = Field(..., min_length=1, max_length=240)
    rationale: list[str] = Field(default_factory=list, max_length=5)
    day_blueprints: list[SplitTemplateDay] = Field(..., min_length=2, max_length=7)


class PromptBundle(BaseModel):
    normalized_input: NormalizedPlanRequest
    candidate_exercises: list[ExerciseCandidate]
    retrieved_context: list[RetrievedContextChunk]
    retrieval_truncated: bool = False
    split_template_matches: list[SplitTemplateMatch] = Field(default_factory=list, max_length=6)



class SplitPlanDay(BaseModel):
    day: DayNameType
    focus: str = Field(..., min_length=1, max_length=80)
    objective: str = Field(..., min_length=1, max_length=180)
    key_patterns: list[str] = Field(..., min_length=1, max_length=4)


class SplitPlan(BaseModel):
    summary: str = Field(..., min_length=1, max_length=220)
    rationale: list[str] = Field(..., min_length=2, max_length=6)
    days: list[SplitPlanDay] = Field(..., min_length=2, max_length=7)


class PlanReview(BaseModel):
    approved: bool
    issues: list[str] = Field(default_factory=list, max_length=8)
    revision_notes: list[str] = Field(default_factory=list, max_length=8)


class PlanExercise(BaseModel):
    name: str = Field(..., min_length=1)
    sets: int = Field(..., ge=1, le=8)
    reps: str = Field(..., min_length=1, max_length=20)
    rest_seconds: int = Field(..., ge=15, le=240)
    intensity_note: str = Field(..., min_length=1, max_length=160)
    primary_muscle_group: str = Field(..., min_length=1, max_length=80)
    secondary_muscles: list[str] = Field(default_factory=list, max_length=5)
    movement_pattern: str = Field(default="", max_length=80)
    equipment_used: str = Field(..., min_length=1, max_length=80)
    coaching_cues: list[str] = Field(default_factory=list, max_length=3)
    exercise_explanation: str = Field(default="", max_length=220)
    substitution_note: str = Field(..., min_length=1, max_length=180)


class PlanDay(BaseModel):
    day: DayNameType
    focus: str = Field(..., min_length=1, max_length=80)
    duration_minutes: int = Field(..., ge=1, le=90)
    warmup: list[str] = Field(..., min_length=2, max_length=5)
    exercises: list[PlanExercise] = Field(..., min_length=2, max_length=6)
    cooldown: list[str] = Field(..., min_length=1, max_length=3)
    coach_notes: list[str] = Field(..., min_length=1, max_length=3)


class PlanMetadata(BaseModel):
    provider_requested: str
    provider_used: str
    model_used: str
    candidate_exercise_count: int = Field(..., ge=0)
    retrieved_chunk_count: int = Field(..., ge=0)
    retrieval_strategy: str
    retrieval_truncated: bool
    generated_at: str


class PlanResponse(BaseModel):
    summary: str
    athlete_snapshot: list[str] = Field(..., min_length=3, max_length=6)
    coaching_notes: list[str] = Field(..., min_length=3, max_length=6)
    days: list[PlanDay] = Field(..., min_length=2, max_length=7)
    metadata: PlanMetadata


class PlanEditSelection(BaseModel):
    day: DayNameType
    focus: str = Field(default="", max_length=80)
    exercise_names: list[str] = Field(default_factory=list, max_length=6)


class PlanEditRequest(BaseModel):
    intake: PlanRequest
    original_plan: PlanResponse
    edit_instructions: str = Field(..., min_length=1, max_length=2000)
    selected_sessions: list[PlanEditSelection] = Field(default_factory=list, max_length=14)
    preserve_unselected: bool = True


class ChatRequest(BaseModel):
    session_id: str
    message: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    response: str
    message_count: int
