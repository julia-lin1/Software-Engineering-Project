# Generated by Django 5.1.1 on 2024-11-05 18:21

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0005_issue_due_date"),
    ]

    operations = [
        migrations.CreateModel(
            name="CalendarEvent",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=100)),
                ("start_date", models.DateField()),
                ("end_date", models.DateField()),
                ("is_meeting", models.BooleanField(default=False)),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="projects.project",
                    ),
                ),
            ],
        ),
    ]