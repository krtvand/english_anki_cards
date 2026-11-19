from conftest import run
from fakes import FakeAnki, FakeClock, FakeLauncher

HEADER = ["english", "russian", "comment", "anki"]


def test_sync_asks_anki_to_sync(make_sheet, anki):
    code, out = run(["sync"], make_sheet(HEADER), anki)

    assert code == 0
    assert out == {"synced": True}
    assert anki.syncs == 1


def test_unreachable_anki_is_launched_once_then_the_command_fails(make_sheet):
    anki = FakeAnki(answering=False)
    launcher = FakeLauncher()
    clock = FakeClock()

    code, out = run(["sync"], make_sheet(HEADER), anki, launch_anki=launcher, clock=clock)

    assert code == 1
    assert "couldn't reach Anki" in out["error"]
    assert launcher.launches == 1
    assert anki.syncs == 0
    assert 15 <= clock.now <= 30  # it waited about 20 s before giving up


def test_anki_that_comes_up_after_launch_lets_the_command_succeed(make_sheet):
    clock = FakeClock()
    anki = FakeAnki(answering=False)
    launcher = FakeLauncher(on_launch=lambda: anki.come_up_at(clock, clock.now + 6))

    code, out = run(["sync"], make_sheet(HEADER), anki, launch_anki=launcher, clock=clock)

    assert code == 0
    assert out == {"synced": True}
    assert launcher.launches == 1
    assert anki.syncs == 1


def test_running_anki_is_not_launched(make_sheet, anki):
    launcher = FakeLauncher()

    run(["sync"], make_sheet(HEADER), anki, launch_anki=launcher)

    assert launcher.launches == 0


def test_next_does_not_need_anki(make_sheet):
    launcher = FakeLauncher()
    sheet = make_sheet(HEADER, ["Take care", "Береги себя", "", ""])

    code, out = run(["next"], sheet, FakeAnki(answering=False), launch_anki=launcher)

    assert code == 0
    assert out["row"] == 2
    assert launcher.launches == 0
