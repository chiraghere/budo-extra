from django.db import models
from django.contrib.auth.models import User


def path_file_name_two(instance, filename):
    return '/'.join(filter(None, ("media", str(instance.task.task_case.id), "documents", str(instance.created_by), filename)))


def path_file_name(instance, filename):
    return '/'.join(filter(None, ("media", str(instance.task.task_case), "images", str(instance.created_by), filename)))


class case(models.Model):
    case_name = models.CharField(max_length=64)
    case_members = models.ManyToManyField(User, related_name='case_members')
    case_clients = models.ManyToManyField(User, related_name='case_clients')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='case_creator')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.case_name


class invite(models.Model):
    choice_key = (
        ('case_member', 'Case_Member'),
        ('case_client', 'Case_Client'),
    )
    case = models.ForeignKey(case, on_delete=models.CASCADE)
    sent_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_to')
    sent_from = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_by')
    position = models.CharField(choices=choice_key, max_length=16)


class task(models.Model):
    billing_choices = (
        ('non billing', 'Non Billing'),
        ('billing', 'Billing'),
    )

    invoice_choices = (
        ('hourly', 'Hourly'),
        ('onetime', 'Onetime')
    )

    task_name = models.CharField(max_length=64)
    details = models.TextField(blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    billing_type = models.CharField(choices=billing_choices, max_length=16, null=True)
    invoice_type = models.CharField(choices=invoice_choices, max_length=16, null=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    task_members = models.ManyToManyField(User, related_name='task_members')
    task_case = models.ForeignKey(case, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='task_created_by')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.task_name


class comments(models.Model):
    task = models.ForeignKey(task, on_delete=models.CASCADE)
    comment = models.CharField(max_length=255)
    comment_user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.id


class checklist(models.Model):
    checklist_name = models.CharField(max_length=64)
    task = models.ForeignKey(task, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.checklist_name


class checklist_items(models.Model):
    checklist = models.ForeignKey(checklist, on_delete=models.CASCADE)
    item = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class task_labels(models.Model):
    task = models.ForeignKey(task, on_delete=models.CASCADE)
    label = models.CharField(max_length=16)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class task_activity(models.Model):
    task = models.ForeignKey(task, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class timer(models.Model):
    status_choices = (
        ('pause', 'Pause'),
        ('end', 'End')
    )
    task = models.ForeignKey(task, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True)
    status = models.CharField(choices=status_choices, max_length=16)


class document(models.Model):
    document = models.FileField(upload_to=path_file_name_two)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    task = models.ForeignKey(task, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class image(models.Model):
    image = models.ImageField(upload_to=path_file_name)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    task = models.ForeignKey(task, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
