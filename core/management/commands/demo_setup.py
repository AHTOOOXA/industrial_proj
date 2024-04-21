import random
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker

from core.models import User, Step, Machine, Detail, Order, OrderEntry, Report, ReportEntry, Plan, PlanEntry, Table


class Command(BaseCommand):
    help = 'Generate random demo data'

    def handle(self, *args, **options):
        faker = Faker()

        User.objects.create_superuser(
            username='admin',
            password='admin',
            role=User.Role.ADMIN,
        )

        # Create random users
        for _ in range(5):
            user = User.objects.create(
                username=faker.unique.last_name(),
                role=faker.random_element(User.Role.choices),
            )
            user.set_password('password')
            user.save()

        # Create random steps
        for _ in range(5):
            Step.objects.create(name=f"Этап {_}")

        # Create random machines for each step
        for step in Step.objects.all():
            for _ in range(random.randint(4, 6)):
                Machine.objects.create(
                    name=f"Станок {_}",
                    step=step,
                )

        # Create random details
        for _ in range(10):
            Detail.objects.create(name=f"{faker.unique.word()} №{(_ + 1) * 10}")

        Table.objects.create(
            current_date=datetime.now(),
            current_step=Step.objects.order_by('?').first(),
        )

        # Create random orders and order entries
        for _ in range(10):
            order_date = faker.date_time_between_dates(
                datetime_start=datetime.now() - timedelta(days=5),
                datetime_end=datetime.now()
            )
            order = Order.objects.create(
                user=User.objects.order_by('?').first(),
                name=faker.word(),
                number=faker.random_number(),
                date=timezone.make_aware(order_date),
                is_active=faker.boolean(),
            )
            for _ in range(random.randint(2, 5)):
                OrderEntry.objects.create(
                    order=order,
                    detail=Detail.objects.order_by('?').first(),
                    quantity=faker.random_int(min=100, max=3000, step=100),
                )

        # Generate reports and plans for each step
        for i, step in enumerate(Step.objects.all()):
            # Create random reports and report entries
            for _ in range(125 // (i + 1)):
                report_date = faker.date_time_between_dates(
                    datetime_start=datetime.now() - timedelta(days=8),
                    datetime_end=datetime.now()
                )
                report = Report.objects.create(
                    user=User.objects.order_by('?').first(),
                    date=timezone.make_aware(report_date),
                    order=Order.objects.order_by('?').first(),
                    step=step,
                )
                for _ in range(random.randint(1, 2)):
                    ReportEntry.objects.create(
                        user=User.objects.order_by('?').first(),
                        report=report,
                        machine=Machine.objects.filter(step=step).order_by('?').first(),
                        detail=Detail.objects.order_by('?').first(),
                        quantity=faker.random_int(min=50, max=500),
                    )

            # Create random plans and plan entries
            for _ in range(50):
                plan_date = faker.date_time_between_dates(
                    datetime_start=datetime.now() - timedelta(days=1),
                    datetime_end=datetime.now() + timedelta(days=4)
                )
                plan = Plan.objects.create(
                    date=timezone.make_aware(plan_date),
                    machine=Machine.objects.filter(step=step).order_by('?').first(),
                    step=step,
                )
                for _ in range(random.randint(1, 2)):
                    PlanEntry.objects.create(
                        plan=plan,
                        detail=Detail.objects.order_by('?').first(),
                        quantity=faker.random_int(min=50, max=500),
                    )

        self.stdout.write(self.style.SUCCESS('Successfully generated demo data'))
