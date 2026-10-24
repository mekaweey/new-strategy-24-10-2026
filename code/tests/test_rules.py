# -*- coding: utf-8 -*-
"""Small, self-contained checks for the rules used by the primary claim.

Run from the package root:
    python -m unittest discover -s code/tests -v

These tests do not re-run the full backtest.  They check the execution rules,
sizing arithmetic, the published headline, and 25 hand-checked trades.
"""
from __future__ import annotations

import json
import math
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code"))
import engine  # noqa: E402


class ExecutionRules(unittest.TestCase):
    def frame(self, **kw):
        base = {"close": 100.0, "next_open": 100.0, "nh14": 100.0,
                "next_p14": 100.0, "og": 0.0}
        base.update(kw)
        return pd.DataFrame([base])

    def test_open_mode(self):
        s = self.frame(next_open=101.0)
        self.assertEqual(float(engine.exit_price(s, "open").iloc[0]), 101.0)

    def test_no_gapdown_always_sells_next_open(self):
        s = self.frame(og=-0.01, next_open=98.0, nh14=105.0)
        self.assertEqual(float(engine.exit_price(s, "limit14", 0.05).iloc[0]), 98.0)

    def test_gapdown_recovery_sells_at_close(self):
        s = self.frame(og=-0.06, next_open=94.0, nh14=101.0, next_p14=96.0)
        self.assertEqual(float(engine.exit_price(s, "limit14", 0.05).iloc[0]), 100.0)

    def test_gapdown_no_recovery_sells_next_14(self):
        s = self.frame(og=-0.06, next_open=94.0, nh14=98.0, next_p14=96.0)
        self.assertEqual(float(engine.exit_price(s, "limit14", 0.05).iloc[0]), 96.0)


class Sizing(unittest.TestCase):
    def test_adv_cap(self):
        g = pd.DataFrame({"close": [10.0], "adv20": [1_000_000.0]})
        qty, capped = engine.size(g, 1_000_000.0, "adapt", 1, 1, 0.02, 0.001, 0.0013)
        self.assertTrue(capped)
        self.assertLessEqual(qty[0], math.floor(0.02 * 1_000_000.0 / (10.0 * 1.001)))

    def test_room_respects_cash_plus_commission(self):
        g = pd.DataFrame({"close": [10.0], "adv20": [1e12]})
        qty, _ = engine.size(g, 100.0, "adapt", 1, 1, 0.02, 0.001, 0.0013)
        self.assertLessEqual(qty[0] * 10.0 * 1.001 * 1.0013, 100.0 + 1e-9)

    def test_fixed_fee_budget_is_outside_size(self):
        # engine.simulate reserves 2 EGP/order before calling size; this test
        # documents the convention used by the ledger.
        g = pd.DataFrame({"close": [10.0], "adv20": [1e12]})
        qty, _ = engine.size(g, 100.0 - 4.0, "adapt", 1, 1, 0.02, 0.001, 0.0013)
        self.assertLessEqual(qty[0] * 10.0 * 1.001 * 1.0013, 96.0 + 1e-9)


class Arithmetic(unittest.TestCase):
    def test_cost_identity(self):
        qty = 100.0
        entry_gross = 10.0
        entry_fill = 10.01
        exit_gross = 11.0
        exit_fill = 10.989
        buy_value = qty * entry_gross
        buy_cost = qty * entry_fill
        sell_value = qty * exit_gross
        sell_proceeds = qty * exit_fill
        gross = sell_value - buy_value
        slip = (buy_cost - buy_value) + (sell_value - sell_proceeds)
        var = 0.0013 * (buy_cost + sell_proceeds)
        net = gross - slip - var - 4.0
        self.assertAlmostEqual(gross, 100.0)
        self.assertAlmostEqual(slip, 2.1)
        self.assertAlmostEqual(var, 2.72987)
        self.assertAlmostEqual(net, 91.17013, places=9)

    def test_metrics_drawdown(self):
        d = pd.DataFrame({
            "date": pd.to_datetime(["2022-01-01", "2022-01-02", "2022-01-03"]),
            "equity": [100.0, 120.0, 90.0], "net": [0.0, 20.0, -30.0],
            "n_trades": [1, 1, 1], "inv": [100, 100, 100], "n": [1, 1, 1],
            "cap_bind": [False, False, False], "max_part": [0.01, 0.01, 0.01],
        })
        m = engine.metrics(d, "x", cap0=100.0)
        self.assertAlmostEqual(m["max_dd"], -0.25)
        self.assertAlmostEqual(m["final"], 90.0)


class PublishedNumbers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = ROOT / "data_derived"

    def test_headline(self):
        e = json.loads((self.d / "expected_headline.json").read_text(encoding="utf-8"))
        self.assertAlmostEqual(e["E1_base"]["final"], 8_034_834.94, places=2)
        self.assertAlmostEqual(e["E1_base"]["profit"], 7_734_834.94, places=2)
        self.assertEqual(e["E1_base"]["trades"], 7413)

    def test_t1_count(self):
        self.assertEqual(len(engine.T1), 69)

    def test_ledger_reconciles(self):
        l = pd.read_csv(self.d / "trades_ledger.csv")
        l = l[l["variant"] == "E1_base"]
        self.assertAlmostEqual(float(l["net"].sum()), 7_734_834.94, places=2)
        self.assertLess(float(l["net_diff_vs_engine"].abs().max()), 1e-6)
        self.assertEqual(int(l["signal_date"].nunique()), 900)
        self.assertEqual(len(l), 7413)

    def test_no_selected_limit_up_and_no_negative_cash(self):
        l = pd.read_csv(self.d / "trades_ledger.csv")
        l = l[l["variant"] == "E1_base"]
        self.assertEqual(int(l["entry_at_close_limit_up"].sum()), 0)
        self.assertGreaterEqual(float(l["equity_after"].min()), 0.0)

    def test_exit_labels(self):
        l = pd.read_csv(self.d / "trades_ledger.csv")
        l = l[l["variant"] == "E1_base"]
        self.assertEqual(int(l["exit_fallback_14"].sum()), 1)
        self.assertEqual(int((l["exit_rule"] == "next_open").sum()), 7387)
        self.assertEqual(int((l["exit_rule"] == "next_p14_after_gap").sum()), 21)

    def test_spot_checks(self):
        s = pd.read_csv(self.d / "spot_checks.csv")
        self.assertEqual(len(s), 25)
        self.assertEqual(s["signal_date"].nunique(), 25)
        self.assertLess(float(s["net_diff2"].abs().max()), 1e-6)
        self.assertEqual(set(s["category"]), {"winning_random", "losing_random",
                                              "largest_profit", "worst_loss"})

    def test_skipped_nights(self):
        l = pd.read_csv(self.d / "trades_ledger.csv")
        l = l[l["variant"] == "E1_base"]
        self.assertEqual(int(l["signal_date"].nunique()) + 252, 1152)


if __name__ == "__main__":
    unittest.main(verbosity=2)
