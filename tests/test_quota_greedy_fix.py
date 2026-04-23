import unittest
from gemini_cli_headless import _is_quota_error, MinuteQuotaExhaustedError

class TestQuotaGreedyFix(unittest.TestCase):
    def test_quota_regex_standalone_429(self):
        # Valid quota errors
        self.assertTrue(_is_quota_error("Error 429: too many requests"))
        self.assertTrue(_is_quota_error("Status: 429"))
        self.assertTrue(_is_quota_error('{"code": 429}'))
        self.assertTrue(_is_quota_error("quota exhausted"))
        self.assertTrue(_is_quota_error("Rate limit reached"))

    def test_quota_regex_false_positives(self):
        # False positives from the bug report
        self.assertFalse(_is_quota_error("session-429-abc-123"))
        self.assertFalse(_is_quota_error("File saved to /tmp/429_report.txt"))
        self.assertFalse(_is_quota_error("Invalid session identifier \"8429b1\""))
        self.assertFalse(_is_quota_error("The number 429 is a prime? No."))

if __name__ == "__main__":
    unittest.main()
