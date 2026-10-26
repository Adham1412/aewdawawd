from app.services import order_states as st


def _rejects(a, b):
    try:
        st.check_transition(a, b)
    except st.InvalidTransition:
        return True
    return False


def test_happy_path_is_allowed():
    path = [st.AWAITING_PAYMENT, st.PAYMENT_SUBMITTED, st.PAID, st.PROCESSING, st.COMPLETED]
    for a, b in zip(path, path[1:]):
        st.check_transition(a, b)


def test_cannot_skip_payment_check():
    assert _rejects(st.AWAITING_PAYMENT, st.PAID)
    assert _rejects(st.AWAITING_PAYMENT, st.COMPLETED)
    assert _rejects(st.PAYMENT_SUBMITTED, st.COMPLETED)


def test_terminal_states_have_no_exit():
    for s in (st.COMPLETED, st.CANCELLED, st.REFUNDED):
        for t in st.ALL_STATUSES:
            assert _rejects(s, t)


def test_refund_requires_prior_payment():
    assert _rejects(st.AWAITING_PAYMENT, st.REFUND_PENDING)
    assert _rejects(st.CANCELLED, st.REFUNDED)
    st.check_transition(st.PAID, st.REFUND_PENDING)
    st.check_transition(st.REFUND_PENDING, st.REFUNDED)


def test_unknown_status_rejected():
    assert _rejects("PAID", "HACKED")
    assert _rejects("HACKED", "PAID")


def test_every_status_has_uzbek_text():
    assert set(st.STATUS_TEXT_UZ) == set(st.ALL_STATUSES)
