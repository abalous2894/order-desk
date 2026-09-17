import pytest

from order_desk.domains.status_lifecycle.service import (
    StatusLifecycleError,
    assert_valid_status,
    assert_valid_transition,
)


def test_valid_status_normalization():
    assert assert_valid_status("Ready for Pickup") == "ready_for_pickup"


def test_invalid_status_raises():
    with pytest.raises(StatusLifecycleError):
        assert_valid_status("lost")


def test_forward_transitions_allowed():
    assert_valid_transition("received", "in_progress")
    assert_valid_transition("in_progress", "ready_for_pickup")
    assert_valid_transition("ready_for_pickup", "completed")


def test_backward_transition_blocked():
    with pytest.raises(StatusLifecycleError):
        assert_valid_transition("completed", "received")


def test_completed_is_terminal():
    with pytest.raises(StatusLifecycleError):
        assert_valid_transition("completed", "in_progress")
