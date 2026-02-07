from app.env.ipd import run_policies


def test_ipd_all_c_vs_all_c_deterministic():
    def all_c(obs, state):
        return "C", state

    r = run_policies(all_c, all_c, rounds=5)
    assert r.cum_a == 15
    assert r.cum_b == 15
    assert [s.act_a for s in r.steps] == ["C"] * 5
    assert [s.act_b for s in r.steps] == ["C"] * 5


def test_ipd_invalid_action_raises():
    def bad(obs, state):
        return "X", state

    def all_c(obs, state):
        return "C", state

    try:
        run_policies(bad, all_c, rounds=1)
        assert False, "expected ValueError"
    except ValueError as e:
        assert str(e) == "invalid_action"


def test_ipd_state_must_be_jsonable():
    def bad_state(obs, state):
        return "C", {"x": set([1])}

    def all_c(obs, state):
        return "C", state

    try:
        run_policies(bad_state, all_c, rounds=1)
        assert False, "expected TypeError"
    except TypeError:
        pass

