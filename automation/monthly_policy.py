"""All automated data queries stop at the end of the last completed UTC month."""
from datetime import datetime, timedelta, timezone

def month_cutoff(now=None):
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError('The run time must include a timezone')
    return now.astimezone(timezone.utc).replace(day=1,hour=0,minute=0,second=0,microsecond=0)

def cutoff_metadata(now=None):
    cutoff=month_cutoff(now)
    return {'data_cutoff_exclusive':cutoff.isoformat(),
            'data_through':(cutoff-timedelta(days=1)).date().isoformat(),
            'data_date_policy':'through_previous_calendar_month_UTC'}

def require_closed_window(acquisition,cutoff,lookahead=timedelta()):
    stamp=datetime.fromisoformat(acquisition.replace('Z','+00:00'))
    if stamp.tzinfo is None or cutoff.tzinfo is None:
        raise ValueError('Explicit timezones are required')
    if stamp>=cutoff or stamp+lookahead>cutoff:
        raise ValueError('The acquisition or required feature window extends beyond the previous-month cutoff')
