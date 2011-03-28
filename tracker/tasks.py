from datetime import timedelta
from celery.decorators import task, periodic_task
from tracker.models import make_daily_report, COLLECT_TIME
from tracker.models import COUNTRY_STATS_TIME, make_monthly_report_country

@periodic_task(run_every=timedelta(seconds=COLLECT_TIME))
def collect_statistic():
    make_daily_report()

@periodic_task(run_every=timedelta(hours=COUNTRY_STATS_TIME))
def generate_country_report():
    make_monthly_report_country(category='links', force=True)
    make_monthly_report_country(category='search', force=True)
    
