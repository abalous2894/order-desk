from order_desk.domains.status_lifecycle.service import allowed_next_statuses, transition_rules


def test_allowed_next_includes_current_and_forward_only():
    assert allowed_next_statuses("received") == ["received", "in_progress", "ready_for_pickup"]
    assert allowed_next_statuses("completed") == ["completed"]


def test_in_progress_orders_ready_before_completed():
    assert allowed_next_statuses("in_progress") == [
        "in_progress",
        "ready_for_pickup",
        "completed",
    ]


def test_transition_rules_cover_all_statuses():
    rules = transition_rules()
    assert set(rules.keys()) == {"received", "in_progress", "ready_for_pickup", "completed"}
    assert rules["completed"] == []


def test_status_lifecycle_rules_api(client):
    res = client.get("/api/v1/status-lifecycle/rules")
    assert res.status_code == 200
    assert res.json()["ready_for_pickup"] == ["completed"]
