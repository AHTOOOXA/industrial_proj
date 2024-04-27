import datetime
from collections import defaultdict

from django.db.models import F, Prefetch
from django.utils.timezone import make_aware

from .models import Machine, Order, Plan, Report, ReportEntry, Step, Table


def get_shift(timestamp: datetime.datetime):
    shift_start = 3  # should be in UTC
    shift_end = shift_start + 12
    hour = timestamp.hour
    if hour < shift_start:
        timestamp -= datetime.timedelta(hours=12)
        return timestamp.replace(hour=shift_end, minute=0, second=0, microsecond=0)
    elif shift_start <= hour < shift_end:
        return timestamp.replace(hour=shift_start, minute=0, second=0, microsecond=0)
    elif hour >= shift_end:
        return timestamp.replace(hour=shift_end, minute=0, second=0, microsecond=0)


class TableCell:
    def __init__(self, shift=None):
        self.report_entries = list()
        self.plan = None
        self.shift = shift

    def get_display(self):
        if self.report_entries and self.plan:
            return {
                "class": "done-plan",
                "report_entries": self.report_entries,
                "plan": self.plan
            }
        if self.report_entries:
            return {
                "class": "done",
                "report_entries": self.report_entries
            }
        elif self.plan:
            return {
                "class": "plan",
                "plan": self.plan
            }
        elif self.shift.hour == 3:
            return {
                "class": "day",
                "text": str(self.shift.strftime("%d.%m"))
            }
        else:
            return {
                "class": "night",
                "text": str(self.shift.strftime("%d.%m"))
            }


def get_shifts_table(shifts_count=28):
    # prep and fetching
    tbl = Table.objects.all().first()
    from_date, step = tbl.current_date, tbl.current_step

    timestamps = [from_date
                  + datetime.timedelta(hours=12 * i) for i in range(0, shifts_count)]
    shifts = [get_shift(timestamp) for timestamp in timestamps]
    machines = Machine.objects.filter(step=step)

    table_empty_cells = {(shift, machine) for machine in machines for shift in shifts}
    cell_dict = defaultdict(lambda: defaultdict(lambda: TableCell()))

    # fetching and inserting report_entries
    report_entries = ReportEntry.objects.filter(
        report__date__range=(timestamps[0], timestamps[-1]),
        report__step=step).select_related("detail").prefetch_related("machine").annotate(
        timestamp=F("report__date")
    )
    for report_entry in report_entries:
        shift = get_shift(report_entry.timestamp)
        table_empty_cells.discard((shift, report_entry.machine))
        cell_dict[shift][report_entry.machine].report_entries.append(report_entry)

    # fetching and inserting plans
    plans = Plan.objects.filter(
        date__range=(timestamps[0], timestamps[-1]),
        step=step).select_related("machine").prefetch_related("planentry_set").prefetch_related("planentry_set__detail")
    for plan in plans:
        shift = get_shift(plan.date)
        table_empty_cells.discard((shift, plan.machine))
        cell_dict[shift][plan.machine].plan = plan

    # --should rewrite to bulk_create
    # filling empty cells with new Plans
    for table_empty_cell in table_empty_cells.copy():
        plan, created = Plan.objects.prefetch_related("planentry_set").get_or_create(
            date=table_empty_cell[0],
            machine=table_empty_cell[1],
            step=step
        )
        shift = get_shift(plan.date)
        table_empty_cells.discard((shift, plan.machine))
        cell_dict[shift][table_empty_cell[1]].plan = plan

    # preparing table for template
    table = []
    for shift in shifts:
        row = [
            TableCell(shift).get_display()
        ]
        for machine in machines:
            row.append(cell_dict[shift][machine].get_display())
        table.append(row)

    return step.id, machines, table


def get_orders_display(is_active=True):
    steps = Step.objects.all().order_by("id")
    orders = Order.objects.filter(is_active=is_active).order_by("-id").prefetch_related(
        "orderentry_set",
        "orderentry_set__detail",
        "report_set",
        Prefetch(
            "report_set",
            queryset=Report.objects.prefetch_related(
                "reportentry_set"
            ).select_related("step"),
            to_attr="prefetched_reports"
        ))

    leftovers = defaultdict(lambda: defaultdict(int))
    for order in orders:
        for order_entry in order.orderentry_set.all():
            for step in steps:
                total_quantity_reported = sum(
                    report_entry.quantity
                    for report in order.prefetched_reports
                    if report.step_id == step.pk
                    for report_entry in report.reportentry_set.all()
                    if report_entry.detail_id == order_entry.detail_id
                )
                leftovers[step.pk][order_entry.pk] = -order_entry.quantity + total_quantity_reported

    return steps, orders, leftovers


# COMPLETE REFACTOR NEEDED
# 100+ SIMILAR QUERIES
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
            shift_reports = Report.objects.filter(
                date__range=(timestamps[i + 1], timestamps[i])).order_by("-date")
        elif user_pk == "-1":
            shift_reports = Report.objects.filter(
                user__isnull=True,
                date__range=(timestamps[i + 1], timestamps[i])).order_by("-date")
        else:
            shift_reports = Report.objects.filter(
                user_id=user_pk,
                date__range=(timestamps[i + 1], timestamps[i])).order_by("-date")
        shift_name = str(timestamps[i + 1].strftime("%d.%m")) + (" День" if timestamps[i + 1].hour < 12 else " Ночь")
        # shift_name += ' ' + str(localtime(timestamps[i + 1])) + '  ' + str(localtime(timestamps[i]))
        if shift_reports:
            shift_reports_lists[shift_name] = {}
            for step in steps:
                shift_step_objs = (shift_reports.filter(step=step).
                                   prefetch_related("reportentry_set",
                                                    "reportentry_set__detail",
                                                    "reportentry_set__machine").
                                   select_related("user",
                                                  "order")
                                   )
                shift_reports_lists[shift_name][step] = shift_step_objs
    return steps, shift_reports_lists
