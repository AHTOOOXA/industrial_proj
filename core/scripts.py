import datetime

from .forms import PlanForm
from .models import Report, Machine, Detail, ReportEntry, Table, Plan


# COMPLETE REFACTOR NEEDED
def get_shifts_table(
        from_date=datetime.datetime.today().replace(hour=0, minute=0, second=0) - datetime.timedelta(days=2),
        shifts_count=24):
    from_date = Table.objects.all()[0].current_date
    table = []
    timestamps = [
        from_date + datetime.timedelta(
            hours=12 * i) for i in range(0, shifts_count)]
    machines = Machine.objects.all()
    for i in range(len(timestamps) - 1):
        row_objs = ReportEntry.objects.filter(
            report__date__range=(timestamps[i], timestamps[i + 1]))
        row = [{
            'class': '',
            # 'text': str(timestamps[i].day) + ('-Д' if timestamps[i].hour < 12 else '-Н')
            'text': str(timestamps[i].strftime('%d.%m')) + (' день' if timestamps[i].hour < 12 else ' ночь')
            # 'text': str(timestamps[i + 1].day) + ('У' if timestamps[i + 1].hour < 12 else 'Н'),
        }]
        for machine in machines:
            objs = row_objs.filter(machine=machine)
            if objs:
                cell = {'class': 'done', 'objs': []}
                for obj in objs:
                    d = {
                        'pk': obj.pk,
                        'detail': obj.detail,
                        'quantity': obj.quantity,
                    }
                    cell['objs'].append(d)
                row.append(cell)
            else:
                plan, created = Plan.objects.get_or_create(
                    machine=machine,
                    date=timestamps[i],
                )
                cell = {
                    'class': 'plan',
                    'plan': plan,
                }
                row.append(cell)
        table.append(row)
    return table
