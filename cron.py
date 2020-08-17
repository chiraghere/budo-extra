from cases.models import *
from datetime import datetime, timedelta, time, date
import pytz
from apscheduler.schedulers.blocking import BlockingScheduler

sched = BlockingScheduler()


@sched.scheduled_job('interval', minutes=5)
def timed_job():
    task_set = task.objects.exclude(due_date__isnull=True)
    for entry in task_set:
        if entry.due_date <= date.today():
            pass

#
# sched.start()
