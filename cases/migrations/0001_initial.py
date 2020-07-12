# Generated by Django 3.0.3 on 2020-07-06 04:59

import cases.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='case',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('case_name', models.CharField(max_length=64)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('case_clients', models.ManyToManyField(related_name='case_clients', to=settings.AUTH_USER_MODEL)),
                ('case_members', models.ManyToManyField(related_name='case_members', to=settings.AUTH_USER_MODEL)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='case_creator', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='checklist',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('checklist_name', models.CharField(max_length=64)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='task',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('task_name', models.CharField(max_length=64)),
                ('details', models.TextField(blank=True, null=True)),
                ('due_date', models.DateField(blank=True, null=True)),
                ('billing_type', models.CharField(choices=[('non billing', 'Non Billing'), ('billing', 'Billing')], max_length=16, null=True)),
                ('invoice_type', models.CharField(choices=[('hourly', 'Hourly'), ('onetime', 'Onetime')], max_length=16, null=True)),
                ('cost', models.DecimalField(decimal_places=2, max_digits=10, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='task_created_by', to=settings.AUTH_USER_MODEL)),
                ('task_case', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cases.case')),
                ('task_members', models.ManyToManyField(related_name='task_members', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='timer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_time', models.DateTimeField()),
                ('end_time', models.DateTimeField(null=True)),
                ('status', models.CharField(choices=[('pause', 'Pause'), ('end', 'End')], max_length=16)),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cases.task')),
            ],
        ),
        migrations.CreateModel(
            name='task_labels',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=16)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cases.task')),
            ],
        ),
        migrations.CreateModel(
            name='task_activity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(max_length=64)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cases.task')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='invite',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position', models.CharField(choices=[('case_member', 'Case_Member'), ('case_client', 'Case_Client')], max_length=16)),
                ('case', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cases.case')),
                ('sent_from', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_by', to=settings.AUTH_USER_MODEL)),
                ('sent_to', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sent_to', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='image',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to=cases.models.path_file_name)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cases.task')),
            ],
        ),
        migrations.CreateModel(
            name='document',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('document', models.FileField(upload_to=cases.models.path_file_name_two)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cases.task')),
            ],
        ),
        migrations.CreateModel(
            name='comments',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comment', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('comment_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cases.task')),
            ],
        ),
        migrations.CreateModel(
            name='checklist_items',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('checklist', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cases.checklist')),
            ],
        ),
        migrations.AddField(
            model_name='checklist',
            name='task',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cases.task'),
        ),
    ]