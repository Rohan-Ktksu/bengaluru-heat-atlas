"""Calendar boundaries and ancillary-data windows must exclude the current month."""
from datetime import datetime, timedelta
import unittest
from monthly_policy import month_cutoff, cutoff_metadata, require_closed_window

class MonthlyPolicyTests(unittest.TestCase):
    def test_previous_month_including_year_rollover_and_leap_year(self):
        for run,through in [('2026-09-15','2026-08-31'),
                            ('2026-10-01','2026-09-30'),
                            ('2027-01-10','2026-12-31'),
                            ('2024-03-01','2024-02-29')]:
            with self.subTest(run=run):
                self.assertEqual(cutoff_metadata(datetime.fromisoformat(run+'T00:00:00+00:00'))['data_through'],through)

    def test_utc_calendar_and_explicit_timezone(self):
        run=datetime.fromisoformat('2026-09-01T02:00:00+05:30')
        self.assertEqual(cutoff_metadata(run)['data_through'],'2026-07-31')
        with self.assertRaises(ValueError): month_cutoff(datetime(2026,9,15))

    def test_cutoff_is_exclusive_and_older_data_remains_eligible(self):
        cutoff=month_cutoff(datetime.fromisoformat('2026-09-15T00:00:00+00:00'))
        for stamp in ['2026-08-31T23:59:59Z','2026-06-04T05:00:00Z']:
            require_closed_window(stamp,cutoff)
        for stamp in ['2026-09-01T00:00:00Z','2026-09-14T05:00:00Z']:
            with self.assertRaises(ValueError): require_closed_window(stamp,cutoff)

    def test_future_feature_windows_cannot_cross_cutoff(self):
        cutoff=month_cutoff(datetime.fromisoformat('2026-09-15T00:00:00+00:00'))
        require_closed_window('2026-08-27T00:00:00Z',cutoff,timedelta(days=5))
        with self.assertRaises(ValueError):
            require_closed_window('2026-08-27T05:00:00Z',cutoff,timedelta(days=5))
        with self.assertRaises(ValueError):
            require_closed_window('2026-08-31T23:00:00Z',cutoff,timedelta(minutes=90))

if __name__=='__main__': unittest.main()
