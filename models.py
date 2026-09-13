from enum import Enum
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid')

class EvidenceStatus(str, Enum):
    FOUND = 'EVIDENCE_FOUND'
    NOT_FOUND = 'NOT_FOUND_IN_UPLOAD'
    VERSION = 'VERSION_MISMATCH'
    MODEL = 'MODEL_MISMATCH'
    UNREADABLE = 'UNREADABLE'
    INSUFFICIENT = 'INSUFFICIENT_INFORMATION'

class ReviewStatus(str, Enum):
    UNREVIEWED = 'UNREVIEWED'
    HUMAN = 'HUMAN_CONFIRMATION_REQUIRED'
    EXPERT = 'EXPERT_JUDGMENT_REQUIRED'
    CONFIRMED = 'CONFIRMED_BY_USER'

class CheckField(StrictModel):
    key: str
    label: str
    question: str

class Requirement(StrictModel):
    requirement_id: str
    requirement_title: str
    requirement_description: str
    regulation_reference: str
    source_url: str
    expert_required: bool
    fields: list[CheckField]

class Project(StrictModel):
    name: str = 'BC-100 EU 기술문서 준비'
    product: str = 'Stand-alone general material-handling belt conveyor'
    model: str = 'BC-100'
    design_revision: str = 'B'
    market: Literal['EU'] = 'EU'
    launch_date: str = '2026-11-01'

class Page(StrictModel):
    number: int
    text: str
    unreadable: bool

class Document(StrictModel):
    name: str
    sha256: str
    pages: list[Page]
    model: str
    design_revision: str

class Evidence(StrictModel):
    document: str
    page: int = Field(ge=1)
    excerpt: str
    reason: str
    field_key: str

class Match(StrictModel):
    requirement_id: str
    evidence: list[Evidence]
    evidence_status: EvidenceStatus
    review_status: ReviewStatus
    issue: str
    missing_information: list[str]
    next_actions: list[str]

class MatchBatch(StrictModel):
    results: list[Match]

class Result(Match):
    requirement_title: str
    requirement_description: str
    regulation_reference: str
    source_url: str
    validation_notes: list[str] = Field(default_factory=list)
    confirmed_at: str | None = None

    @property
    def has_gap(self):
        return self.evidence_status != EvidenceStatus.FOUND or bool(self.missing_information)

class DraftPlan(StrictModel):
    # AI can choose/order facts; it cannot author new engineering facts.
    ordered_fact_ids: list[str]

class Analysis(StrictModel):
    analysis_id: str
    created_at: str
    mode: Literal['mock', 'openai']
    model: str
    project: Project
    dataset_version: str
    documents: list[Document]
    results: list[Result]
    duration_seconds: float
    warnings: list[str]
