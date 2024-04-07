# Generated by Django 4.2.9 on 2024-02-20 16:28

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0014_table_current_step"),
    ]

    operations = [
        migrations.AddField(
            model_name="plan",
            name="step",
            field=models.ForeignKey(
                default=1, on_delete=django.db.models.deletion.CASCADE, to="core.step"
            ),
            preserve_default=False,
        ),
    ]