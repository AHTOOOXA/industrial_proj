# Generated by Django 4.2.9 on 2024-01-26 07:06

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_detail_machine_order_orderentry_report_reportentry_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[
                    ("ADMIN", "Администратор"),
                    ("MODERATOR", "Модератор"),
                    ("WORKER", "Рабочий"),
                ],
                default="WORKER",
                max_length=50,
            ),
        ),
    ]
