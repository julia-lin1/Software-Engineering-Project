# Generated by Django 5.1.1 on 2024-10-31 05:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0002_remove_issue_created_at_remove_issue_created_by_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="issue",
            name="status",
            field=models.CharField(
                choices=[("open", "Open"), ("completed", "Completed")],
                default="open",
                max_length=50,
            ),
        ),
    ]
