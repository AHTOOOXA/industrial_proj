import datetime

from django.utils.timezone import make_aware

from .models import Machine, OrderEntry, Plan, Report, ReportEntry, Step, Table


# COMPLETE REFACTOR NEEDED
# REWORK PAGINATION
def get_shifts_table(
        shifts_count=28):
    from_date = Table.objects.all()[0].current_date
    step = Table.objects.all()[0].current_step
    table = []
    timestamps = [
        from_date + datetime.timedelta(
            hours=12 * i) for i in range(0, shifts_count)]
    machines = Machine.objects.filter(step=step)
    for i in range(len(timestamps) - 1):
        row_report_entries = ReportEntry.objects.filter(
            report__date__range=(timestamps[i], timestamps[i + 1]),
            report__step=step)
        if timestamps[i].hour < 12:
            txt = str(timestamps[i].strftime("%d.%m")) + " день"
            txt = str(timestamps[i].strftime("%d.%m"))
            cls = "day"
        else:
            txt = str(timestamps[i].strftime("%d.%m")) + " ночь"
            txt = str(timestamps[i].strftime("%d.%m"))
            cls = "night"
        row = [{
            "class": cls,
            "text": txt
        }]
        for machine in machines:
            report_entries = row_report_entries.filter(machine=machine)
            if report_entries:
                cell = {"class": "done", "report_entries": []}
                for report_entry in report_entries:
                    d = {
                        "pk": report_entry.pk,
                        "detail": report_entry.detail,
                        "quantity": report_entry.quantity,
                    }
                    cell["report_entries"].append(d)
                row.append(cell)
            else:
                plan, created = Plan.objects.get_or_create(
                    machine=machine,
                    date=timestamps[i],
                    step=step,
                )
                cell = {
                    "class": "plan",
                    "plan": plan,
                }
                row.append(cell)
        table.append(row)
    return step.pk, machines, table


def get_leftovers():
    steps = Step.objects.all()
    leftovers = {}
    for step in steps:
        leftovers[step.pk] = {}
    for order_entry in OrderEntry.objects.all():
        for step in steps:
            leftovers[step.pk][order_entry.pk] = -order_entry.quantity
            for report_entry in ReportEntry.objects.filter(report__order=order_entry.order, report__step=step,
                                                           detail=order_entry.detail):
                # print('hello', order_entry.detail, report_entry.detail, report_entry.quantity)
                leftovers[step.id][order_entry.pk] += report_entry.quantity
    return leftovers


# COMPLETE REFACTOR NEEDED
# REWORK PAGINATION
def get_reports_view(shifts_count=10, page=1, user_pk=None):
    # getting close to cur_time based on Table.current_date to correctly sep shifts
    from_date = Table.objects.all()[0].current_date
    cur_time = datetime.datetime.today().replace(hour=0, minute=0, second=0)
    cur_time = make_aware(cur_time)
    while from_date < cur_time:
        from_date += datetime.timedelta(hours=12)
    from_date += datetime.timedelta(hours=24)
    from_date -= datetime.timedelta(hours=((page - 1) * shifts_count - (page - 1)) * 12)
    timestamps = [from_date - datetime.timedelta(hours=12 * i) for i in range(0, shifts_count)]

    steps = Step.objects.all()
    shift_reports_lists = {}
    for i in range(len(timestamps) - 1):
        if not user_pk:
            shift_objs = Report.objects.filter(
                date__range=(timestamps[i + 1], timestamps[i])).order_by("-date")
        elif user_pk == "-1":
            shift_objs = Report.objects.filter(
                user__isnull=True,
                date__range=(timestamps[i + 1], timestamps[i])).order_by("-date")
        else:
            shift_objs = Report.objects.filter(
                user_id=user_pk,
                date__range=(timestamps[i + 1], timestamps[i])).order_by("-date")
        shift_name = str(timestamps[i + 1].strftime("%d.%m")) + (" День" if timestamps[i + 1].hour < 12 else " Ночь")
        # shift_name += ' ' + str(localtime(timestamps[i + 1])) + '  ' + str(localtime(timestamps[i]))
        if shift_objs:
            shift_reports_lists[shift_name] = {}
            for step in steps:
                shift_step_objs = shift_objs.filter(step=step)
                shift_reports_lists[shift_name][step] = shift_step_objs
    return steps, shift_reports_lists
