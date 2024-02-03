import datetime
from .models import Report, Machine, Detail, ReportEntry, Table


def get_shifts_table(
        from_date=datetime.datetime.today().replace(hour=0, minute=0, second=0) - datetime.timedelta(days=2),
        shifts_count=24):
    from_date = Table.objects.all()[0].current_date
    table = []
    timestamps = [
         from_date + datetime.timedelta(
            hours=12 * i) for i in range(0, shifts_count)]
    for i in range(len(timestamps) - 1):
        row_objs = ReportEntry.objects.filter(
            report__date__range=(timestamps[i], timestamps[i + 1]))
        row = [{
            'class': '',
            'text': str(timestamps[i].day) + (' утро' if timestamps[i].hour < 12 else ' ночь'),
        }]
        machines = Machine.objects.all()
        for machine in machines:
            objs = row_objs.filter(machine=machine)
            if objs:
                s = ''
                for obj in objs:
                    s += str(obj.detail) + '\n' + str(obj.quantity) + '\n'
                d = {
                    'class': 'done',
                    'text': s,
                }
                row.append(d)
            else:
                d = {
                    'class': '',
                    'text': '',
                }
                row.append(d)
        table.append(row)
    return table
