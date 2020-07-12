from django.core.management.base import BaseCommand, CommandError
import datetime
from cases.models import task


class Command(BaseCommand):
    help = 'crosscheck due date'

    # def add_arguments(self, parser):
    #     parser.add_argument('task_id', type=int)

    def handle(self, *args, **options):
        task_set = task.objects.all()
        for current_task in task_set:
            print(type(current_task.due_date))
            if datetime.date.today() >= current_task.due_date:
                print("alert")
            else:
                print("not yet")