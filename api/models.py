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

WorkoutLocationType = Literal["Home", "Apartment gym", "Commercial gym", "Outdoors"]

CardioPreferenceType = Literal[
    "No cardio preference",
    "Enjoys cardio",
    "Low-impact only",
    "Prefer minimal cardio",
]

IntensityPreferenceType = Literal["Light", "Moderate", "Challenging"]

VarietyPreferenceType = Literal["Keep it simple", "Mix it up", "No preference"]

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
]


class SessionResponse(BaseModel):
    session_id: str
    created_at: str


class PlanRequest(BaseModel):
    experience: ExperienceType
    equipment: list[EquipmentType] = Field(..., min_length=1, max_length=10)
    age_range: AgeRangeType
    height_feet: int = Field(..., ge=3, le=8)
    height_inches: int = Field(..., ge=0, le=11)
    weight_lbs: int = Field(..., ge=50, le=700)
    days_per_week: int = Field(..., ge=2, le=6)
    session_length: int = Field(..., ge=20, le=90)
    available_training_days: list[DayNameType] = Field(..., min_length=2, max_length=6)
    flexible_training_days: list[DayNameType] = Field(default_factory=list, max_length=3)
    injuries: str = ""
    current_activity_level: ActivityLevelType
    workout_location: WorkoutLocationType
    equipment_details: str = ""
    cardio_preference: CardioPreferenceType
    intensity_preference: IntensityPreferenceType
    variety_preference: VarietyPreferenceType
    notes: str = ""


class NormalizedAthleteProfile(BaseModel):
    experience: ExperienceType
    age_range: AgeRangeType
    height_feet: int = Field(..., ge=3, le=8)
    height_inches: int = Field(..., ge=0, le=11)
    weight_lbs: int = Field(..., ge=50, le=700)
    current_activity_level: ActivityLevelType


class NormalizedConstraints(BaseModel):
    equipment: list[EquipmentType] = Field(..., min_length=1, max_length=10)
    workout_location: WorkoutLocationType
    equipment_details: str
    days_per_week: int = Field(..., ge=2, le=6)
    session_length: int = Field(..., ge=20, le=90)
    available_training_days: list[DayNameType] = Field(..., min_length=2, max_length=6)
    flexible_training_days: list[DayNameType] = Field(default_factory=list, max_length=3)
    injuries: str


class NormalizedPreferences(BaseModel):
    cardio_preference: CardioPreferenceType
    intensity_preference: IntensityPreferenceType
    variety_preference: VarietyPreferenceType
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
    difficulty: str = Field(..., min_length=1, max_length=40)
    movement_pattern: str = Field(..., min_length=1, max_length=80)
    suitable_goals: list[str] = Field(default_factory=list, max_length=6)
    coaching_cues: list[str] = Field(default_factory=list, max_length=4)
    contraindications: list[str] = Field(default_factory=list, max_length=5)


class RetrievedContextChunk(BaseModel):
    source_id: str
    title: str
    score: float = Field(..., ge=0)
    content: str = Field(..., min_length=1)
    movement_pattern: str = Field(..., min_length=1, max_length=80)
    equipment_used: str = Field(..., min_length=1, max_length=80)


class PromptBundle(BaseModel):
    system_prompt: str
    user_prompt: str
    normalized_input: NormalizedPlanRequest
    candidate_exercises: list[ExerciseCandidate]
    retrieved_context: list[RetrievedContextChunk]
    retrieval_truncated: bool = False


class PlanExercise(BaseModel):
    name: str = Field(..., min_length=1)
    sets: int = Field(..., ge=1, le=8)
    reps: str = Field(..., min_length=1, max_length=20)
    rest_seconds: int = Field(..., ge=15, le=240)
    intensity_note: str = Field(..., min_length=1, max_length=160)
    primary_muscle_group: str = Field(..., min_length=1, max_length=80)
    equipment_used: str = Field(..., min_length=1, max_length=80)
    substitution_note: str = Field(..., min_length=1, max_length=180)


class PlanDay(BaseModel):
    day: DayNameType
    focus: str = Field(..., min_length=1, max_length=80)
    duration_minutes: int = Field(..., ge=20, le=90)
    warmup: list[str] = Field(..., min_length=2, max_length=5)
    exercises: list[PlanExercise] = Field(..., min_length=3, max_length=6)
    cooldown: list[str] = Field(..., min_length=1, max_length=3)
    coach_notes: list[str] = Field(..., min_length=1, max_length=3)


class PlanMetadata(BaseModel):
    provider_requested: str
    provider_used: str
    model_used: str
    fallback_used: bool
    fallback_reason: str = ""
    candidate_exercise_count: int = Field(..., ge=0)
    retrieved_chunk_count: int = Field(..., ge=0)
    retrieval_strategy: str
    retrieval_truncated: bool
    generated_at: str


class PlanResponse(BaseModel):
    summary: str
    athlete_snapshot: list[str] = Field(..., min_length=3, max_length=6)
    coaching_notes: list[str] = Field(..., min_length=3, max_length=6)
    days: list[PlanDay] = Field(..., min_length=2, max_length=6)
    optional_days: list[PlanDay] = Field(default_factory=list, max_length=3)
    metadata: PlanMetadata


class ChatRequest(BaseModel):
    session_id: str
    message: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    response: str
    message_count: int
