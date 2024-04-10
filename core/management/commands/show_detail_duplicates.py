from django.core.management.base import BaseCommand
from core.models import Detail


class Command(BaseCommand):
    help = 'Show detail duplicates'

    def handle(self, *args, **options):
        details = Detail.objects.all()

        details_by_name = dict()

        for detail in details:
            if detail.name not in details_by_name:
                details_by_name[detail.name] = []
            details_by_name[detail.name].append(detail)

        for key, value in details_by_name.items():
            if len(value) > 1:
                print(f"Detail {key} has duplicates:")
                print(f"{value[0].pk}: {value[0]} will be saved")
                for detail in value[1:]:
                    print(f"    {detail.pk}: {detail} will be merged with {value[0].pk}")
