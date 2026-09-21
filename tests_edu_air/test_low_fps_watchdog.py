"""LowFpsWatchdog: auto-enables low-CPU mode once per session after FPS
stays sustained-low -- the priority-haute item from the project audit
("descendre la résolution webcam automatiquement si FPS < 20"), verified
here without needing a real camera/pipeline."""

from __future__ import annotations

from edu_air.ui import LowFpsWatchdog


def make_watchdog(**kw) -> LowFpsWatchdog:
    kw.setdefault("threshold", 20.0)
    kw.setdefault("grace_s", 3.0)
    kw.setdefault("warmup_s", 3.0)
    return LowFpsWatchdog(**kw)


def test_never_triggers_during_startup_warmup():
    wd = make_watchdog()
    t = 0.0
    for _ in range(50):
        assert wd.observe(cursor_fps=5.0, now=t, performance_mode_on=False) is False
        t += 0.1
    assert t < wd.warmup_s + 5.0  # sanity: we never left the warmup window here
    assert not wd.triggered


def test_triggers_after_sustained_low_fps_past_warmup():
    wd = make_watchdog(threshold=20.0, grace_s=3.0, warmup_s=3.0)
    t = 0.0
    fired_at = None
    while t < 10.0:
        fired = wd.observe(cursor_fps=10.0, now=t, performance_mode_on=False)
        if fired:
            fired_at = t
            break
        t += 0.2
    assert fired_at is not None
    assert fired_at >= 3.0 + 3.0 - 0.2   # warmup + grace, minus one step of slack
    assert wd.triggered


def test_never_fires_twice():
    wd = make_watchdog(warmup_s=0.0, grace_s=0.5)
    t = 0.0
    results = []
    while t < 5.0:
        results.append(wd.observe(cursor_fps=5.0, now=t, performance_mode_on=False))
        t += 0.2
    assert results.count(True) == 1


def test_a_brief_dip_does_not_trigger():
    """A one-frame FPS dip is normal jitter, not a sustained problem."""
    wd = make_watchdog(threshold=20.0, grace_s=3.0, warmup_s=0.0)
    assert wd.observe(cursor_fps=10.0, now=0.0, performance_mode_on=False) is False
    assert wd.observe(cursor_fps=10.0, now=0.5, performance_mode_on=False) is False
    # Recovers before the grace window elapses -> the low streak resets.
    assert wd.observe(cursor_fps=30.0, now=1.0, performance_mode_on=False) is False
    assert wd.observe(cursor_fps=10.0, now=1.2, performance_mode_on=False) is False
    assert wd.observe(cursor_fps=10.0, now=3.0, performance_mode_on=False) is False
    assert not wd.triggered


def test_never_fires_while_performance_mode_already_on():
    """Whether the teacher turned it on manually or it was auto-triggered
    earlier, the watchdog must never fight that state."""
    wd = make_watchdog(warmup_s=0.0, grace_s=0.0)
    assert wd.observe(cursor_fps=5.0, now=0.0, performance_mode_on=True) is False
    assert wd.observe(cursor_fps=5.0, now=1.0, performance_mode_on=True) is False
    assert not wd.triggered


def test_does_not_retrigger_after_teacher_turns_it_back_off():
    """Once triggered, the watchdog must stay quiet even if performance_mode
    later flips back to False -- it must never re-fight a deliberate choice
    to turn low-CPU mode back off."""
    wd = make_watchdog(warmup_s=0.0, grace_s=0.5)
    t = 0.0
    while not wd.triggered and t < 5.0:
        wd.observe(cursor_fps=5.0, now=t, performance_mode_on=False)
        t += 0.2
    assert wd.triggered
    # Teacher manually turns it back off -- FPS is still bad.
    assert wd.observe(cursor_fps=5.0, now=t + 1.0, performance_mode_on=False) is False
    assert wd.observe(cursor_fps=5.0, now=t + 5.0, performance_mode_on=False) is False


def test_healthy_fps_never_triggers():
    wd = make_watchdog(warmup_s=0.0, grace_s=1.0)
    t = 0.0
    while t < 10.0:
        assert wd.observe(cursor_fps=30.0, now=t, performance_mode_on=False) is False
        t += 0.2
    assert not wd.triggered


def test_zero_fps_at_startup_is_ignored_not_treated_as_low():
    """cursor_fps starts at exactly 0.0 before the EMA has a single sample;
    that must not itself read as "critically low FPS"."""
    wd = make_watchdog(warmup_s=0.0, grace_s=0.5)
    assert wd.observe(cursor_fps=0.0, now=0.0, performance_mode_on=False) is False
    assert wd.observe(cursor_fps=0.0, now=1.0, performance_mode_on=False) is False
    assert not wd.triggered
