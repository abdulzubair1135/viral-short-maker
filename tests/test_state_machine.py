import pytest
from backend.app.core.state_machine import ProjectState, StateMachine, StateMachineError

def test_valid_transitions():
    assert StateMachine.can_transition(ProjectState.DRAFT, ProjectState.ANALYZING)
    assert StateMachine.can_transition(ProjectState.ANALYZING, ProjectState.CANDIDATE)
    assert StateMachine.can_transition(ProjectState.CANDIDATE, ProjectState.SELECTED)
    assert StateMachine.can_transition(ProjectState.SELECTED, ProjectState.RENDERING)
    assert StateMachine.can_transition(ProjectState.RENDERING, ProjectState.QUALITY_CHECK)
    assert StateMachine.can_transition(ProjectState.QUALITY_CHECK, ProjectState.READY)
    assert StateMachine.can_transition(ProjectState.READY, ProjectState.APPROVED)

def test_illegal_transitions():
    assert not StateMachine.can_transition(ProjectState.DRAFT, ProjectState.PUBLISHED)
    assert not StateMachine.can_transition(ProjectState.DRAFT, ProjectState.READY)
    assert not StateMachine.can_transition(ProjectState.ANALYZING, ProjectState.PUBLISHED)

def test_rights_confirmation_blocking():
    # Attempting transition to PUBLISHED with unconfirmed rights should be strictly blocked
    with pytest.raises(StateMachineError) as exc:
        StateMachine.transition(ProjectState.APPROVED, ProjectState.PUBLISHED, rights_confirmed=False)
    assert "without confirmed content rights" in str(exc.value)

    # With confirmed rights, transition succeeds
    res = StateMachine.transition(ProjectState.APPROVED, ProjectState.PUBLISHED, rights_confirmed=True)
    assert res == ProjectState.PUBLISHED
