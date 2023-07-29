import csv
from django.core.management.base import BaseCommand
from django.conf import settings
from core.models import Car


class Command(BaseCommand):
    help = "Loads car data from CSV file"

    def handle(self, *args, **options):
        datafile = settings.BASE_DIR / 'core' / 'data' / 'cars.csv'

        with open(datafile) as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                Car.objects.get_or_create(manufacturer=row[0], country=row[1])