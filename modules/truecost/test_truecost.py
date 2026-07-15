import sys
sys.dont_write_bytecode = True

# ----------------------------------------------------------------------------
# test_truecost.py: self-contained, stdlib-only regression suite for truecost.py.
#
# Run it from anywhere:  python3 test_truecost.py
#
# Ground rules this suite enforces on itself:
#   - It NEVER reads the real ~/.claude/projects or ~/.claude/truecost. Every
#     test builds synthetic transcripts in a temp dir and redirects the tool
#     there (tc.HOME / tc.BASE for in-process tests, HOME / TRUECOST_HOME env
#     vars for subprocess tests).
#   - It writes nothing into the skill folder. setUpModule snapshots the folder
#     and tearDownModule asserts the listing is unchanged (no __pycache__, no
#     stray data files).
#   - Stdlib only, Python 3.8+.
#
# The star of the suite is the phantom-idle regression test in
# TestActiveSeconds: a live ancestor of this tool credited min(gap, IDLE_CAP)
# for EVERY idle gap, so every night and weekend silently added 15 minutes of
# "work", inflating measured hours by roughly 28%.
# ----------------------------------------------------------------------------

import contextlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from datetime import datetime, timezone

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_PATH = os.path.join(TEST_DIR, "truecost.py")

# A fixed, timezone-explicit anchor: 2026-01-05 10:00:00 UTC.
T0 = int(datetime(2026, 1, 5, 10, 0, 0, tzinfo=timezone.utc).timestamp())

# A cwd that exists on nobody's machine. Repo naming must work from the cwd
# recorded inside the transcript, without ever consulting the filesystem.
# Deliberately NOT a user-home-directory shape: the kit's scrub gate denies
# machine-path literals anywhere under modules/ (including spelling those shapes
# out in a comment — this one learned that firsthand), and rightly so. The path
# is never resolved, only read back out of a synthetic transcript, so any
# absolute path that does not exist will do.
FAKE_ROOT = "/tmp/nobody-truecost-test"

# One valid billing profile, reused across tests. Chosen so every intermediate
# value is exact in binary floating point: 120 / 0.5 = 240, 240 / 120 = 2,
# break-even 242, rate 363, and a 2 h project quotes at exactly 726.
VALID_PROFILE = {
    "currency": "USD",
    "wage": 120.0,
    "utilization": 0.5,
    "billable_h_month": 120.0,
    "stack_usd_mo": 240.0,
    "markup": 0.5,
}

tc = None            # the module under test, loaded in setUpModule
_BEFORE = None       # skill-folder snapshot, taken before anything runs
_SENTINEL = None     # throwaway dir the module globals point at by default


def _snapshot(root):
    """Recursive listing of names (files AND dirs) under root."""
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        rel = os.path.relpath(dirpath, root)
        for n in list(filenames) + list(dirnames):
            out.append(os.path.normpath(os.path.join(rel, n)))
    return sorted(out)


def setUpModule():
    global tc, _BEFORE, _SENTINEL
    _BEFORE = _snapshot(TEST_DIR)

    spec = importlib.util.spec_from_file_location("truecost_under_test", SCRIPT_PATH)
    tc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tc)

    # truecost binds HOME and BASE at import time, from the real home. Point
    # them at a nonexistent sandbox immediately so that no test, however
    # buggy, can ever read the real ~/.claude.
    _SENTINEL = tempfile.mkdtemp(prefix="truecost-sentinel-")
    tc.HOME = os.path.join(_SENTINEL, "no-such-home")
    tc.BASE = os.path.join(tc.HOME, ".claude", "projects")
    os.environ["TRUECOST_HOME"] = os.path.join(_SENTINEL, "no-such-data")
    tc._MAP, tc._AMBIG = None, []
    tc._UNPRICED.clear()


def tearDownModule():
    if _SENTINEL:
        shutil.rmtree(_SENTINEL, ignore_errors=True)
    if _BEFORE is None:
        return
    after = _snapshot(TEST_DIR)
    if after != _BEFORE:
        added = sorted(set(after) - set(_BEFORE))
        removed = sorted(set(_BEFORE) - set(after))
        raise AssertionError(
            "HYGIENE: the skill folder changed during the test run. "
            "added=%r removed=%r" % (added, removed))


# ---------------------------------------------------------------- helpers
def U(ts, side=False, typed=True, text="do the thing"):
    """A main-thread (or sidechain) user event in load()'s internal format."""
    return dict(ts=float(ts), kind="u", cost=0.0, side=side, typed=typed, text=text)


def A(ts, side=False, model="claude-sonnet-5", cost=0.0, usage=None):
    """An assistant event in load()'s internal format."""
    return dict(ts=float(ts), kind="a", model=model, usage=usage, cost=cost, side=side)


def iso(epoch):
    return datetime.fromtimestamp(epoch, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def j_user(epoch, text, cwd, source="typed", side=False):
    """A user line as it appears in a real transcript JSONL."""
    return {"timestamp": iso(epoch), "type": "user", "isSidechain": side,
            "promptSource": source, "cwd": cwd, "message": {"content": text}}


def j_asst(epoch, model="claude-sonnet-5", usage=None, side=False):
    """An assistant line as it appears in a real transcript JSONL."""
    if usage is None:
        usage = {"input_tokens": 100, "output_tokens": 200,
                 "cache_read_input_tokens": 0}
    return {"timestamp": iso(epoch), "type": "assistant", "isSidechain": side,
            "message": {"model": model, "usage": usage}}


def write_jsonl(path, records):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for r in records:
            fh.write((r if isinstance(r, str) else json.dumps(r)) + "\n")


def capture(fn, *args, **kwargs):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        fn(*args, **kwargs)
    return buf.getvalue()


def run_cli(args, home, data_home):
    """Run truecost.py in a subprocess with a fully crafted environment."""
    env = {
        "HOME": home,
        "TRUECOST_HOME": data_home,
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONIOENCODING": "utf-8",
    }
    return subprocess.run(
        [sys.executable, SCRIPT_PATH] + list(args),
        capture_output=True, encoding="utf-8", errors="replace",
        env=env, cwd=home, timeout=60)


class TempEnvTestCase(unittest.TestCase):
    """Per-test sandbox: fresh fake HOME, fake projects dir, fresh data dir.

    Patches tc.HOME / tc.BASE (bound at import in truecost.py) and the
    TRUECOST_HOME env var, resets the module-level caches, and restores
    everything afterwards.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="truecost-suite-")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.home = os.path.join(self.tmp, "home")
        self.projects = os.path.join(self.home, ".claude", "projects")
        os.makedirs(self.projects)
        self.data_home = os.path.join(self.tmp, "truecost-data")
        os.makedirs(self.data_home)

        self._saved = (tc.HOME, tc.BASE, os.environ.get("TRUECOST_HOME"))
        tc.HOME, tc.BASE = self.home, self.projects
        os.environ["TRUECOST_HOME"] = self.data_home
        tc._MAP, tc._AMBIG = None, []
        tc._UNPRICED.clear()
        self.addCleanup(self._restore)

    def _restore(self):
        tc.HOME, tc.BASE = self._saved[0], self._saved[1]
        if self._saved[2] is None:
            os.environ.pop("TRUECOST_HOME", None)
        else:
            os.environ["TRUECOST_HOME"] = self._saved[2]
        tc._MAP, tc._AMBIG = None, []
        tc._UNPRICED.clear()

    def write_transcript(self, cwd, records, name="session.jsonl"):
        """Place a transcript at $HOME/.claude/projects/<slug>/<name>."""
        slug = cwd.replace("/", "-")
        path = os.path.join(self.projects, slug, name)
        write_jsonl(path, records)
        return path

    def write_profile(self, profile):
        path = os.path.join(self.data_home, "profile.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(profile, fh)
        return path


# ================================================== 1. active_seconds
class TestActiveSeconds(unittest.TestCase):

    def test_multi_day_gap_contributes_zero_phantom_hours_regression(self):
        """THE regression this suite exists for.

        A live ancestor of active_seconds() summed min(gap, IDLE_CAP), which
        credited 15 minutes of "work" for EVERY idle gap: every night, every
        weekend, every pause between projects. Measured hours came out ~28%
        inflated. Two main-thread events three days apart must contribute
        exactly ZERO active seconds, never the cap.
        """
        ev = [U(T0), A(T0 + 3 * 86400)]
        self.assertEqual(tc.active_seconds(ev), 0.0)

    def test_phantom_gap_not_capped_in_mixed_stream(self):
        """Short gaps count, the multi-day gap in the middle adds nothing.

        Under the old min(gap, cap) bug this stream would have reported
        600 + 900 + 600 = 2100 s. Correct is 600 + 0 + 600 = 1200 s.
        """
        ev = [A(T0), A(T0 + 600), A(T0 + 600 + 3 * 86400),
              A(T0 + 1200 + 3 * 86400)]
        self.assertEqual(tc.active_seconds(ev), 1200.0)

    def test_short_gaps_count_fully(self):
        ev = [U(T0), A(T0 + 300), U(T0 + 900)]
        self.assertEqual(tc.active_seconds(ev), 900.0)

    def test_gap_of_exactly_idle_cap_counts(self):
        ev = [U(T0), A(T0 + int(tc.IDLE_CAP))]
        self.assertEqual(tc.active_seconds(ev), tc.IDLE_CAP)

    def test_gap_one_second_over_cap_contributes_zero(self):
        ev = [U(T0), A(T0 + int(tc.IDLE_CAP) + 1)]
        self.assertEqual(tc.active_seconds(ev), 0.0)

    def test_sidechain_events_never_add_active_time(self):
        """Subagent turns run while you wait: they must add zero active time,
        and they must not bridge an idle gap between main-thread events."""
        side = [A(T0 + i * 60, side=True) for i in range(1, 6)]
        ev = sorted([U(T0), U(T0 + 3 * 86400)] + side, key=lambda e: e["ts"])
        self.assertEqual(tc.active_seconds(ev), 0.0)
        self.assertEqual(tc.active_seconds(side), 0.0)


# ================================================== 2. blocks()
class TestBlocks(unittest.TestCase):

    def test_split_into_separate_blocks_across_idle_gap(self):
        ev = [U(T0), A(T0 + 600), U(T0 + 2600), A(T0 + 3200)]
        bl = tc.blocks(ev)
        self.assertEqual(len(bl), 2)
        self.assertEqual([e["ts"] for e in bl[0]], [float(T0), float(T0 + 600)])
        self.assertEqual([e["ts"] for e in bl[1]], [float(T0 + 2600), float(T0 + 3200)])

    def test_sidechain_attaches_to_enclosing_block_for_cost_not_time(self):
        side = A(T0 + 300, side=True, cost=1.25)
        ev = [U(T0), side, A(T0 + 600, cost=0.50), U(T0 + 2600), A(T0 + 3200)]
        bl = tc.blocks(ev)
        self.assertEqual(len(bl), 2)
        self.assertIn(side, bl[0])
        self.assertNotIn(side, bl[1])
        # Cost: the sidechain turn is billed to the block it ran inside.
        cost0 = sum(e["cost"] for e in bl[0] if e["kind"] == "a")
        self.assertAlmostEqual(cost0, 1.75)
        # Time: attaching it must not change the block's active seconds.
        self.assertEqual(tc.active_seconds(bl[0]), 600.0)

    def test_sidechain_in_idle_gap_attaches_to_no_block(self):
        stray = A(T0 + 1500, side=True, cost=5.0)
        ev = [U(T0), A(T0 + 600), stray, U(T0 + 2600), A(T0 + 3200)]
        bl = tc.blocks(ev)
        self.assertEqual(len(bl), 2)
        for b in bl:
            self.assertNotIn(stray, b)

    def test_no_main_thread_events_gives_no_blocks(self):
        self.assertEqual(tc.blocks([]), [])
        self.assertEqual(tc.blocks([A(T0, side=True)]), [])


# ================================================== 3. _pct
class TestPct(unittest.TestCase):

    def test_median_of_two_is_linear_interpolation(self):
        """Nearest-rank rounding up gave 3.0 here and told the user to triple
        every estimate on the strength of one miss. Must be 1.75."""
        self.assertAlmostEqual(tc._pct([0.5, 3.0], .50), 1.75)

    def test_empty_list_returns_zero(self):
        self.assertEqual(tc._pct([], .50), 0.0)

    def test_interpolation_and_unsorted_input(self):
        self.assertAlmostEqual(tc._pct([3.0, 1.0, 2.0], .50), 2.0)
        self.assertAlmostEqual(tc._pct([1, 2, 3, 4, 5], .80), 4.2)
        self.assertAlmostEqual(tc._pct([2.0], .80), 2.0)


# ================================================== 4. price() / _rate()
class TestPricing(TempEnvTestCase):

    def test_hand_computed_cost_known_model(self):
        """All five token classes, at their documented multipliers:
        input 1x, cache read 0.1x, 5m write 1.25x, 1h write 2x, output 1x.
        Expected cost is derived from the PRICES table so the test survives
        a stranger updating the list prices."""
        model = "claude-sonnet-5"
        self.assertIn(model, tc.PRICES, "fixture model was removed from PRICES")
        pin, pout = tc.PRICES[model]
        usage = {"input_tokens": 1000, "output_tokens": 2000,
                 "cache_read_input_tokens": 50000,
                 "cache_creation": {"ephemeral_5m_input_tokens": 10000,
                                    "ephemeral_1h_input_tokens": 4000}}
        expected = (1000 * pin
                    + 50000 * pin * 0.10
                    + 10000 * pin * 1.25
                    + 4000 * pin * 2.00
                    + 2000 * pout) / 1e6
        self.assertAlmostEqual(tc.price(usage, model), expected, places=12)

    def test_legacy_cache_creation_field_assumed_5m(self):
        """Without the cache_creation breakdown, cache_creation_input_tokens
        is priced as a 5m write (1.25x): the cheaper assumption."""
        model = "claude-sonnet-5"
        pin, _ = tc.PRICES[model]
        usage = {"cache_creation_input_tokens": 8000}
        self.assertAlmostEqual(tc.price(usage, model),
                               8000 * pin * 1.25 / 1e6, places=12)

    def test_dated_model_id_resolves_by_prefix(self):
        self.assertEqual(tc._rate("claude-sonnet-5-20260101"),
                         tc.PRICES["claude-sonnet-5"])
        # Same property for whatever the longest key in the table is, so the
        # test keeps meaning even if the table is edited.
        k = max(tc.PRICES, key=len)
        self.assertEqual(tc._rate(k + "-20991231"), tc.PRICES[k])
        # Prefix hits are priced, so they must not be flagged as unpriced.
        self.assertNotIn("claude-sonnet-5-20260101", tc._UNPRICED)

    def test_unknown_model_priced_at_table_ceiling_and_flagged(self):
        ghost = "claude-zz-imaginary-99"
        self.assertEqual(tc._rate(ghost), tc.DEFAULT_PRICE)
        self.assertIn(ghost, tc._UNPRICED)

    def test_placeholder_model_ids_never_flagged(self):
        for m in ("?", "", None):
            self.assertEqual(tc._rate(m), tc.DEFAULT_PRICE)
        self.assertEqual(len(tc._UNPRICED), 0)

    def test_default_price_ceilings_every_row_per_component(self):
        """The PROPERTY, not the implementation.

        The old assertion was `DEFAULT_PRICE == max(PRICES.values())`, which just
        restates the code and therefore can never fail. What the docs actually
        promise is: at least as expensive as every row, per component.
        """
        for k, (pin, pout) in tc.PRICES.items():
            self.assertGreaterEqual(tc.DEFAULT_PRICE[0], pin, f"input under-prices {k}")
            self.assertGreaterEqual(tc.DEFAULT_PRICE[1], pout, f"output under-prices {k}")

    def test_ceiling_is_componentwise_not_lexicographic(self):
        """The case a tuple max() gets wrong: a cheap input with a dear output.

        Every row in the shipped table is exactly 5x out/in, so lexicographic and
        componentwise agree today and the bug is invisible. Add one row that breaks
        the ratio and they diverge: max() keeps the old output price and would
        silently UNDERSTATE output, the dominant term in most turns.
        """
        trap = dict(tc.PRICES)
        trap["claude-trap-1"] = (8.00, 100.00)
        self.assertEqual(tc._ceiling(trap)[1], 100.00)
        self.assertLess(max(trap.values())[1], tc._ceiling(trap)[1])

    def test_lexical_extension_is_not_a_prefix_hit(self):
        """A future id that merely EXTENDS a key is a different model.

        "claude-opus-4-10" starts with the key "claude-opus-4-1". An unbounded
        startswith() would bill it at the 4-1 rate and, worse, suppress the unpriced
        warning, because a prefix hit never reaches _UNPRICED. It must fall through
        to the ceiling and be flagged.
        """
        self.assertIn("claude-opus-4-1", tc.PRICES)
        ext = "claude-opus-4-10"
        # It must resolve to NO table key. (Asserting on the returned price alone
        # would be vacuous here: the ceiling currently equals the opus-4-1 row, so
        # the buggy and the correct code return the same tuple. The tell is the key
        # and the warning, not the number.)
        self.assertIsNone(tc._match_key(ext))
        self.assertEqual(tc._rate(ext), tc.DEFAULT_PRICE)
        self.assertIn(ext, tc._UNPRICED)

    def test_recognised_suffixes_still_resolve(self):
        """A boundary must not break the ids that legitimately carry a suffix."""
        k = "claude-sonnet-5"
        for variant in (k + "-20260101", k + "[1m]", k + "-20260101[1m]"):
            self.assertEqual(tc._rate(variant), tc.PRICES[k], variant)
            self.assertNotIn(variant, tc._UNPRICED)

    def test_null_token_field_does_not_crash_the_report(self):
        """A present-but-null token count is legal JSON and must not kill the run.

        `u.get("input_tokens", 0)` returns None for an explicit null, which then
        multiplies into a TypeError and takes down the entire report over one field
        in one turn.
        """
        u = {"input_tokens": None, "output_tokens": 100,
             "cache_read_input_tokens": None, "cache_creation_input_tokens": None}
        cost = tc.price(u, "claude-sonnet-5")
        self.assertAlmostEqual(cost, 100 * 15.00 / 1e6)

    def test_dated_and_undated_ids_group_as_one_model(self):
        """Per-model attribution must key on the canonical id.

        Keying on the raw string splits one model across two rows, each carrying a
        fraction of the turns. The grand total stays correct, which is precisely why
        nobody notices.
        """
        ev = [A(T0, model="claude-sonnet-5", cost=1.0,
                usage={"input_tokens": 10, "output_tokens": 20}),
              A(T0 + 1, model="claude-sonnet-5-20260101", cost=2.0,
                usage={"input_tokens": 30, "output_tokens": 40})]
        bm = tc.totals(ev)
        self.assertEqual(list(bm), ["claude-sonnet-5"])
        self.assertEqual(bm["claude-sonnet-5"]["turns"], 2)
        self.assertEqual(bm["claude-sonnet-5"]["inp"], 40)
        self.assertEqual(bm["claude-sonnet-5"]["out"], 60)


# ================================================== load() parsing
class TestLoad(TempEnvTestCase):

    def test_parses_prices_and_sorts_synthetic_transcript(self):
        cwd = FAKE_ROOT + "/code/loadrepo"
        model = "claude-sonnet-5"
        pin, pout = tc.PRICES[model]
        usage = {"input_tokens": 1000, "output_tokens": 2000,
                 "cache_read_input_tokens": 50000,
                 "cache_creation": {"ephemeral_5m_input_tokens": 10000,
                                    "ephemeral_1h_input_tokens": 0}}
        # Written deliberately OUT of order: the earliest event is last.
        path = self.write_transcript(cwd, [
            j_user(T0 + 100, "second prompt", cwd),
            j_asst(T0 + 200, model=model, usage=usage),
            j_asst(T0 + 300, side=True),
            j_user(T0, "first prompt", cwd),
        ])
        ev = tc.load([path])
        self.assertEqual(len(ev), 4)
        self.assertEqual([e["ts"] for e in ev],
                         sorted(e["ts"] for e in ev))
        self.assertEqual(ev[0]["text"], "first prompt")
        self.assertTrue(ev[0]["typed"])
        priced = next(e for e in ev if e["kind"] == "a" and not e["side"])
        expected = (1000 * pin + 50000 * pin * 0.10
                    + 10000 * pin * 1.25 + 2000 * pout) / 1e6
        self.assertAlmostEqual(priced["cost"], expected, places=12)
        sides = [e for e in ev if e["side"]]
        self.assertEqual(len(sides), 1)

    def test_user_text_normalization_and_truncation(self):
        cwd = FAKE_ROOT + "/code/loadrepo2"
        listy = {"timestamp": iso(T0 + 100), "type": "user",
                 "promptSource": "hook",
                 "message": {"content": [
                     {"type": "text", "text": "from a"},
                     {"type": "tool_result", "content": "ignored"},
                     {"type": "text", "text": "list"}]}}
        path = self.write_transcript(cwd, [
            j_user(T0, "add   stripe\ncheckout   now", cwd),
            listy,
            j_user(T0 + 200, "y" * 200, cwd),
        ])
        ev = tc.load([path])
        self.assertEqual(ev[0]["text"], "add stripe checkout now")
        self.assertEqual(ev[1]["text"], "from a list")
        self.assertFalse(ev[1]["typed"])      # promptSource "hook" is not typed
        self.assertEqual(len(ev[2]["text"]), 90)

    def test_malformed_and_untimestamped_lines_skipped(self):
        cwd = FAKE_ROOT + "/code/loadrepo3"
        path = self.write_transcript(cwd, [
            j_user(T0, "good line", cwd),
            "this is not json {{{",
            {"type": "user", "message": {"content": "no timestamp"}},
            {"timestamp": "yesterday", "type": "user",
             "message": {"content": "unparseable timestamp"}},
            j_asst(T0 + 60),
        ])
        ev = tc.load([path])
        self.assertEqual(len(ev), 2)
        self.assertEqual([e["kind"] for e in ev], ["u", "a"])


# ================================================== 5. r_estimate pooling
class TestEstimate(TempEnvTestCase):

    def _history(self):
        cwd = FAKE_ROOT + "/code/histrepo"
        rec = []
        prompts = ["alpha payment integration",       # matches phrasing 1
                   "beta gateway rework",             # matches phrasing 2
                   "alpha payment beta gateway combined"]  # matches BOTH
        for i, prompt in enumerate(prompts):
            base = T0 + i * 5000                      # 5000 s apart: separate blocks
            rec.append(j_user(base, prompt, cwd))
            rec.append(j_asst(base + 100))
            rec.append(j_asst(base + 200))            # 200 s active: above noise floor
        self.write_transcript(cwd, rec)

    def test_pipe_query_pools_phrasings_each_block_once(self):
        self._history()
        out = capture(tc.r_estimate, "alpha payment | beta gateway")
        self.assertIn("pooled from 2 phrasings", out)
        self.assertIn("n = 3 comparable blocks", out)
        # The block matched by BOTH phrasings appears exactly once.
        self.assertEqual(out.count("alpha payment beta gateway"), 1)
        self.assertIn("alpha payment integration", out)
        self.assertIn("beta gateway rework", out)

    def test_no_match_prints_estimating_blind(self):
        self._history()
        out = capture(tc.r_estimate, "zzzblorp quuxflux")
        self.assertIn("estimating BLIND", out)


# ================================================== 6. repo naming
class TestRepoNaming(TempEnvTestCase):

    def _seed(self):
        for cwd in (FAKE_ROOT + "/code/myapp",
                    FAKE_ROOT + "/clients/acme/web",
                    FAKE_ROOT + "/clients/globex/web"):
            self.write_transcript(cwd, [j_user(T0, "hello task", cwd),
                                        j_asst(T0 + 60)])

    def test_cwd_from_transcript_names_repo_without_filesystem(self):
        """The cwd inside the transcript is authoritative. The path does not
        exist on this machine, and the name must still resolve to 'myapp'."""
        self._seed()
        m = tc.repo_map()
        self.assertIn("myapp", m)
        self.assertEqual(len(m["myapp"]), 1)

    def test_same_basename_different_cwds_do_not_merge(self):
        """acme/web and globex/web are two different clients. Summing them
        under one 'web' row is how the wrong client gets invoiced."""
        self._seed()
        m = tc.repo_map()
        self.assertIn("acme/web", m)
        self.assertIn("globex/web", m)
        self.assertNotIn("web", m)
        self.assertNotEqual(m["acme/web"], m["globex/web"])

    def test_repos_lookup_exact_and_ambiguous(self):
        self._seed()
        found = tc.repos(["myapp"])
        self.assertEqual(set(found), {"myapp"})
        # An ambiguous name returns BOTH, reported separately, never summed.
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            found = tc.repos(["web"])
        self.assertEqual(set(found), {"acme/web", "globex/web"})
        self.assertIn("DIFFERENT working directories", out.getvalue())


# ================================================== 7. the profile gate (CLI)
class TestLive(TempEnvTestCase):
    """--live must resolve its transcript dir the way every other read does.

    The old code guessed the dir name with `cwd.replace("/", "-")`. Claude Code's
    slug folds "." and "_" to "-" as well, so the guess missed for any repo path
    carrying one: --live printed "no transcripts" and exited 0, which from the
    outside is indistinguishable from an honest empty history. Resolving by the cwd
    recorded INSIDE the transcript is correct under any slug rule.
    """

    def test_live_dir_resolves_a_path_the_naive_slug_would_miss(self):
        cwd = FAKE_ROOT + "/my_app.v2"
        slug = re.sub(r"[/._]", "-", cwd)          # the slug Claude Code writes
        path = os.path.join(self.projects, slug, "session.jsonl")
        write_jsonl(path, [j_user(T0, "hi", cwd), j_asst(T0 + 10)])

        naive = os.path.join(self.projects, cwd.replace("/", "-"))
        self.assertFalse(os.path.isdir(naive), "the old guess must not find it")

        self.assertEqual(tc.live_dir(cwd), os.path.dirname(path))

    def test_live_dir_is_none_when_nothing_matches(self):
        self.assertIsNone(tc.live_dir(FAKE_ROOT + "/never-opened"))


# ================================================== 7. no-profile / bad-input gate
class TestGate(TempEnvTestCase):
    """No profile means no billing commands, full stop. Exit 2, point at
    --setup, and never fall back to a shipped default rate card."""

    def test_quote_without_profile_exits_2_and_mentions_setup(self):
        res = run_cli(["ghostrepo", "--quote"], self.home, self.data_home)
        self.assertEqual(res.returncode, 2, res.stdout + res.stderr)
        self.assertIn("--setup", res.stdout)

    def test_clients_without_profile_exits_2_and_mentions_setup(self):
        res = run_cli(["--clients"], self.home, self.data_home)
        self.assertEqual(res.returncode, 2, res.stdout + res.stderr)
        self.assertIn("--setup", res.stdout)

    def test_wage_override_does_not_bypass_gate(self):
        res = run_cli(["ghostrepo", "--quote", "--wage", "500"],
                      self.home, self.data_home)
        self.assertEqual(res.returncode, 2, res.stdout + res.stderr)
        self.assertIn("--setup", res.stdout)


# ================================================== 7b. overrides face the predicates
class TestOverrideValidation(TempEnvTestCase):
    """A CLI override is an input like any other, so it faces the same predicates
    the profile had to pass.

    profile_errors() enforces wage > 0 and markup >= 0 on the stored profile, but
    the one-off overrides used to walk straight past it. --wage 0 did not crash: it
    printed a confident invoice for nothing. A wrong number stated calmly is the
    exact failure this tool exists to prevent, so it must refuse and say why.
    """

    def setUp(self):
        super().setUp()
        self.write_profile(VALID_PROFILE)
        self.cwd = FAKE_ROOT + "/code/quoterepo"
        rec = [j_user(T0, "some real work", self.cwd)]
        rec += [j_asst(T0 + i * 600) for i in range(1, 13)]
        self.write_transcript(self.cwd, rec)

    def _refused(self, *flags):
        res = run_cli(["quoterepo", "--quote", *flags], self.home, self.data_home)
        self.assertEqual(res.returncode, 2,
                         f"{flags} was ACCEPTED:\n{res.stdout}{res.stderr}")
        out = res.stdout + res.stderr
        self.assertIn("refusing to quote", out)
        # It must refuse BEFORE doing any work: a full report followed by a refusal
        # reads as a partial success, and the reader keeps the number they saw.
        self.assertNotIn("ACTIVE TIME", out.upper())
        self.assertNotIn("TOTAL", out.upper())
        return out

    def test_zero_wage_is_refused_not_quoted_at_zero(self):
        out = self._refused("--wage", "0")
        self.assertIn("wage must be > 0", out)

    def test_negative_wage_is_refused(self):
        self._refused("--wage", "-100")

    def test_negative_markup_is_refused(self):
        out = self._refused("--markup", "-1")
        self.assertIn("markup must be >= 0", out)

    def test_negative_offline_hours_are_refused(self):
        out = self._refused("--offline", "-5")
        self.assertIn("--offline", out)

    def test_non_positive_fx_is_refused(self):
        out = self._refused("--fx", "0")
        self.assertIn("--fx", out)

    def test_a_valid_override_still_quotes(self):
        """The guard must not become a wall: good overrides still work."""
        res = run_cli(["quoterepo", "--quote", "--wage", "150", "--markup", "0"],
                      self.home, self.data_home)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertNotIn("refusing to quote", res.stdout)


# ================================================== 8. quote arithmetic (CLI)
class TestQuoteArithmetic(TempEnvTestCase):
    """fee = ((wage / utilization) + (stack / billable_h)) * (1 + markup) * hours,
    checked against numbers printed by the real CLI."""

    HOURS = 2.0

    def setUp(self):
        super().setUp()
        self.write_profile(VALID_PROFILE)
        cwd = FAKE_ROOT + "/code/quoterepo"
        rec = [j_user(T0, "build the quote fixture", cwd)]
        # 12 more events, 600 s apart: 12 gaps of 600 s = 7200 s = 2.0 h active.
        rec += [j_asst(T0 + i * 600) for i in range(1, 13)]
        self.write_transcript(cwd, rec)

    @staticmethod
    def expected_rate(profile, wage=None):
        w = profile["wage"] if wage is None else wage
        be = (w / profile["utilization"]
              + profile["stack_usd_mo"] / profile["billable_h_month"])
        return be * (1 + profile["markup"])

    @staticmethod
    def fee_from(stdout):
        m = re.search(r">>>\s+\$([\d,]+) USD", stdout)
        if not m:
            raise AssertionError("no fee line in output:\n" + stdout)
        return int(m.group(1).replace(",", ""))

    def test_fee_matches_hand_computed_arithmetic(self):
        res = run_cli(["quoterepo", "--quote"], self.home, self.data_home)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        rate = self.expected_rate(VALID_PROFILE)                 # 363.0
        self.assertEqual(self.fee_from(res.stdout),
                         int(round(rate * self.HOURS)))          # 726
        self.assertIn("${:,.2f}/h".format(rate), res.stdout)     # $363.00/h
        self.assertRegex(res.stdout, r"= BILLABLE\s+2\.0 h")

    def test_offline_hours_add_to_billable(self):
        res = run_cli(["quoterepo", "--quote", "--offline", "1"],
                      self.home, self.data_home)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        rate = self.expected_rate(VALID_PROFILE)
        self.assertEqual(self.fee_from(res.stdout),
                         int(round(rate * (self.HOURS + 1.0))))  # 1089
        self.assertRegex(res.stdout, r"= BILLABLE\s+3\.0 h")

    def test_wage_override_moves_fee_and_is_labelled(self):
        res = run_cli(["quoterepo", "--quote", "--wage", "240"],
                      self.home, self.data_home)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        rate = self.expected_rate(VALID_PROFILE, wage=240.0)     # 723.0
        self.assertEqual(self.fee_from(res.stdout),
                         int(round(rate * self.HOURS)))          # 1446
        self.assertIn("[OVERRIDE]", res.stdout)


# ================================================== 9. ledger round trip
class _FrozenClock(object):
    """Stands in for the time module inside truecost, so two predictions land
    in the same integer second deterministically."""

    def __init__(self, t):
        self._t = t

    def time(self):
        return self._t


class TestLedger(TempEnvTestCase):

    def _freeze(self, epoch):
        saved = tc.time
        tc.time = _FrozenClock(float(epoch))
        self.addCleanup(setattr, tc, "time", saved)

    def test_two_predictions_same_second_get_distinct_ids(self):
        self._freeze(1767600000)
        with contextlib.redirect_stdout(io.StringIO()):
            tc.r_predict("task one", 2.0, "repoA", "post-recon")
            tc.r_predict("task two", 4.0, "repoA", "post-recon")
        recs = tc._ledger()
        self.assertEqual(len(recs), 2)
        ids = [r["id"] for r in recs]
        self.assertEqual(len(set(ids)), 2, "colliding ledger ids: %r" % ids)
        self.assertEqual(ids[0], "e1767600000")
        self.assertEqual(ids[1], "e1767600000-1")

    def test_settle_sets_ratio_and_calibration_reports(self):
        with contextlib.redirect_stdout(io.StringIO()):
            tc.r_predict("round trip task", 2.0, "repoA", "post-recon")
        eid = tc._ledger()[0]["id"]
        out = capture(tc.r_settle, eid, 3.0)
        self.assertIn("UNDER", out)
        rec = tc._ledger()[0]
        self.assertEqual(rec["actual_h"], 3.0)
        self.assertAlmostEqual(rec["ratio"], 1.5)
        self.assertIn("settled_at", rec)
        cal = capture(tc.r_calibration)
        self.assertIn("CALIBRATION", cal)
        self.assertIn("post-recon", cal)
        self.assertIn("median ratio 1.50", cal)

    def test_settle_bogus_id_exits_1_without_traceback(self):
        res = run_cli(["--settle", "e0-bogus", "--actual", "1"],
                      self.home, self.data_home)
        self.assertEqual(res.returncode, 1, res.stdout + res.stderr)
        self.assertIn("no such estimate", res.stdout)
        self.assertNotIn("Traceback", res.stderr)


# ================================================== 10. profile validation
class TestProfileValidation(TempEnvTestCase):

    def test_zero_wage_rejected(self):
        """A hand-written 0 divides by zero three functions later. Refuse it."""
        bad = dict(VALID_PROFILE, wage=0)
        errs = tc.profile_errors(bad)
        self.assertTrue(any("wage" in e for e in errs), errs)
        self.write_profile(bad)
        self.assertIsNone(tc.load_profile(loud=False))

    def test_zero_utilization_rejected(self):
        errs = tc.profile_errors(dict(VALID_PROFILE, utilization=0))
        self.assertTrue(any("utilization" in e for e in errs), errs)
        errs = tc.profile_errors(dict(VALID_PROFILE, utilization=1.5))
        self.assertTrue(any("utilization" in e for e in errs), errs)

    def test_valid_profile_accepted(self):
        self.assertEqual(tc.profile_errors(dict(VALID_PROFILE)), [])
        self.write_profile(VALID_PROFILE)
        p = tc.load_profile(loud=False)
        self.assertIsNotNone(p)
        self.assertEqual(p["wage"], VALID_PROFILE["wage"])

    def test_non_usd_currency_requires_fx(self):
        bad = dict(VALID_PROFILE, currency="CAD")
        errs = tc.profile_errors(bad)
        self.assertTrue(any("fx_to_usd" in e for e in errs), errs)
        ok = dict(VALID_PROFILE, currency="CAD", fx_to_usd=0.73)
        self.assertEqual(tc.profile_errors(ok), [])

    def test_setup_from_json_rejects_bad_profile_writes_nothing(self):
        bad_path = os.path.join(self.tmp, "bad_profile.json")
        with open(bad_path, "w", encoding="utf-8") as fh:
            json.dump(dict(VALID_PROFILE, wage=0), fh)
        res = run_cli(["--setup", "--from-json", bad_path],
                      self.home, self.data_home)
        self.assertEqual(res.returncode, 2, res.stdout + res.stderr)
        self.assertIn("not usable", res.stdout)
        self.assertFalse(
            os.path.exists(os.path.join(self.data_home, "profile.json")),
            "a rejected profile must not be written")


if __name__ == "__main__":
    unittest.main(verbosity=2)
