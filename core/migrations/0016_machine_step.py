# Generated by Django 4.2.9 on 2024-02-21 05:41

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0015_plan_step"),
    ]

    operations = [
        migrations.AddField(
            model_name="machine",
            name="step",
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.SET_NULL, to="core.step"
            ),
        ),
    ]