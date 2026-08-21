"""Tests for Finch payroll withholding demo."""

import unittest
from oa_client import OAClient
import withholding_check
import finch_client


class FinchPayrollDemoTests(unittest.TestCase):
    def setUp(self):
        self.oa = OAClient(token=None)
        self.plan = self.oa.start("Validate payroll FICA withholding", "US")
        slug = (self.plan.get("skills_to_load") or [None])[0]
        self.skill = self.oa.get_skill(slug)

    def test_mock_oa_client(self):
        self.assertEqual(self.plan["jurisdiction"], "US")
        self.assertEqual(self.skill["tier"], 1)
        self.assertIn("Amir Pelinkovic", self.skill["verifier"])

    def test_ss_overwithheld_past_wage_base(self):
        facts = {
            "name": "Sarah Mifsud",
            "gross": 8000.0,
            "ytd_prior_gross": 180000.0,
            "withheld_social_security": 496.0,
            "withheld_medicare": 116.0,
        }
        res = withholding_check.check(facts, self.skill)
        ss_chk = next(c for c in res["checks"] if c["tax"] == "Social Security")
        self.assertEqual(ss_chk["status"], "warn")
        self.assertIn("over-withheld", ss_chk["note"])

    def test_medicare_additional_underwithheld(self):
        facts = {
            "name": "Dave Romero",
            "gross": 15000.0,
            "ytd_prior_gross": 205000.0,
            "withheld_social_security": 0.0,
            "withheld_medicare": 217.50,
        }
        res = withholding_check.check(facts, self.skill)
        mc_chk = next(c for c in res["checks"] if c["tax"] == "Medicare")
        self.assertEqual(mc_chk["status"], "warn")
        self.assertIn("under-withheld", mc_chk["note"])

    def test_regular_fica_ok(self):
        facts = {
            "name": "Lena Park",
            "gross": 5000.0,
            "ytd_prior_gross": 40000.0,
            "withheld_social_security": 310.0,
            "withheld_medicare": 72.50,
        }
        res = withholding_check.check(facts, self.skill)
        self.assertTrue(all(c["status"] == "ok" for c in res["checks"]))

    def test_sample_extraction(self):
        stmts = finch_client.extract("samples/pay_statements.json")
        self.assertEqual(len(stmts), 4)
        norm = finch_client.normalize(stmts[0])
        self.assertEqual(norm["name"], "Sarah Mifsud")


if __name__ == "__main__":
    unittest.main()
