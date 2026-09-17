from enum import Enum
from typing import Dict, Set, Optional

class ProjectState(str, Enum):
    DRAFT = "DRAFT"
    ANALYZING = "ANALYZING"
    CANDIDATE = "CANDIDATE"
    SELECTED = "SELECTED"
    EDITING = "EDITING"
    RENDERING = "RENDERING"
    QUALITY_CHECK = "QUALITY_CHECK"
    READY = "READY"
    APPROVED = "APPROVED"
    UPLOADING = "UPLOADING"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    PAUSED_HUMAN_INTERVENTION = "PAUSED_HUMAN_INTERVENTION"

VALID_TRANSITIONS: Dict[ProjectState, Set[ProjectState]] = {
    ProjectState.DRAFT: {ProjectState.ANALYZING, ProjectState.FAILED, ProjectState.CANCELLED},
    ProjectState.ANALYZING: {ProjectState.CANDIDATE, ProjectState.PAUSED_HUMAN_INTERVENTION, ProjectState.FAILED, ProjectState.CANCELLED},
    ProjectState.PAUSED_HUMAN_INTERVENTION: {ProjectState.ANALYZING, ProjectState.FAILED, ProjectState.CANCELLED},
    ProjectState.CANDIDATE: {ProjectState.SELECTED, ProjectState.ANALYZING, ProjectState.FAILED, ProjectState.CANCELLED},
    ProjectState.SELECTED: {ProjectState.EDITING, ProjectState.RENDERING, ProjectState.FAILED, ProjectState.CANCELLED},
    ProjectState.EDITING: {ProjectState.RENDERING, ProjectState.SELECTED, ProjectState.FAILED, ProjectState.CANCELLED},
    ProjectState.RENDERING: {ProjectState.QUALITY_CHECK, ProjectState.FAILED, ProjectState.CANCELLED},
    ProjectState.QUALITY_CHECK: {ProjectState.READY, ProjectState.FAILED, ProjectState.CANCELLED},
    ProjectState.READY: {ProjectState.APPROVED, ProjectState.EDITING, ProjectState.RENDERING, ProjectState.FAILED},
    ProjectState.APPROVED: {ProjectState.UPLOADING, ProjectState.PUBLISHED, ProjectState.EDITING, ProjectState.READY},
    ProjectState.UPLOADING: {ProjectState.PUBLISHED, ProjectState.FAILED, ProjectState.CANCELLED},
    ProjectState.PUBLISHED: set(),
    ProjectState.FAILED: {ProjectState.DRAFT, ProjectState.ANALYZING, ProjectState.SELECTED, ProjectState.EDITING, ProjectState.RENDERING},
    ProjectState.CANCELLED: {ProjectState.DRAFT, ProjectState.ANALYZING, ProjectState.SELECTED, ProjectState.EDITING},
}

class StateMachineError(Exception):
    pass

class StateMachine:
    @staticmethod
    def can_transition(from_state: ProjectState, to_state: ProjectState) -> bool:
        if from_state == to_state:
            return True
        allowed = VALID_TRANSITIONS.get(from_state, set())
        return to_state in allowed

    @staticmethod
    def transition(current_state: ProjectState, target_state: ProjectState, rights_confirmed: bool = True) -> ProjectState:
        # Rule: Publishing/uploading strictly requires rights_confirmed
        if target_state in {ProjectState.UPLOADING, ProjectState.PUBLISHED} and not rights_confirmed:
            raise StateMachineError("Cannot transition to UPLOADING or PUBLISHED without confirmed content rights!")

        if not StateMachine.can_transition(current_state, target_state):
            raise StateMachineError(f"Illegal state transition from {current_state} to {target_state}")

        return target_state
