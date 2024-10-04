import datetime
import logging
import re
from collections import defaultdict

from django.db.models import F, Prefetch
from django.utils.timezone import make_aware
from transliterate import translit

from .models import Machine, Order, Plan, PlanEntry, Report, ReportEntry, Step, Table

logger = logging.getLogger(__name__)


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


def get_html_id(date, machine) -> str:
    return re.sub(
        "[^(a-z)(A-Z)(0-9)._-]", "",
        date.strftime("shift-%Y-%m-%d-%H-%M-%S-") + translit(str(machine), "ru", reversed=True))


class TableCell:
    def __init__(self, date=None, plan=None, report_entries=None):
        self.report_entries = report_entries
        if not report_entries:
            self.report_entries = list()
        self.plan = plan
        self.date = date

    def get_display(self):
        if self.report_entries or self.plan:
            return {
                "id": get_html_id(get_shift(self.plan.date), self.plan.machine),
                "class": "done-plan",
                "report_entries": self.report_entries,
                "plan": self.plan
            }
        else:
            return {
                "class": "day" if self.date.hour == 3 else "night",
                "text": str(self.date.strftime("%d.%m"))
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

    # fetching and inserting report_entries
    report_entries = ReportEntry.objects.filter(
        report__date__range=(timestamps[0], timestamps[-1]),
        report__step=step).select_related("detail").select_related("report__order").prefetch_related(
        "machine").annotate(
        timestamp=F("report__date")
    )
    for report_entry in report_entries:
        shift = get_shift(report_entry.timestamp)
        cell_dict[shift][report_entry.machine].report_entries.append(report_entry)

    # preparing table for template
    table = []
    for shift in shifts:
        row = [
            TableCell(date=shift).get_display()
        ]
        for machine in machines:
            try:
                row.append(cell_dict[shift][machine].get_display())
            except Exception as e:
                logger.error(f"Error processing cell for shift {shift} and machine {machine}: {str(e)}", exc_info=True)
        table.append(row)

    return step.id, machines, table


def get_orders_display(is_active=True, order_id=None):
    steps = Step.objects.all().order_by("id")

    query = Order.objects
    if order_id:
        query = query.filter(id=order_id)

    orders = query.filter(is_active=is_active).order_by("-id").prefetch_related(
        "orderentry_set",
        "orderentry_set__detail",
        "report_set",
        Prefetch(
            "report_set",
            queryset=Report.objects.prefetch_related(
                "reportentry_set"
            ).select_related("step"),
            to_attr="prefetched_reports"
        ),
        "planentry_set",
        Prefetch(
            "planentry_set",
            queryset=PlanEntry.objects.prefetch_related(
                "plan"
            ).select_related("plan__step"),
            to_attr="prefetched_planentries"
        )
    )

    leftovers = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    orders_stats = defaultdict(lambda: defaultdict(int))
    for step in steps:
        dates = {get_shift(report.date)
                 for order in orders
                 for report in order.prefetched_reports
                 if report.step.pk == step.pk}
        for order in orders:
            for order_entry in order.orderentry_set.all():
                total_quantity_reported = sum(
                    report_entry.quantity
                    for report in order.prefetched_reports
                    if report.step_id == step.pk
                    for report_entry in report.reportentry_set.all()
                    if report_entry.detail_id == order_entry.detail_id
                )
                leftovers[step.pk][order_entry.pk]["reports"] = (-order_entry.quantity
                                                                 + total_quantity_reported)
                total_quantity_planned = sum(
                    plan_entry.quantity if get_shift(plan_entry.plan.date) not in dates else 0
                    for plan_entry in order.prefetched_planentries
                    if plan_entry.detail_id == order_entry.detail_id
                    and plan_entry.plan.step_id == step.pk
                )
                leftovers[step.pk][order_entry.pk]["reports_and_plans"] = (-order_entry.quantity
                                                                           + total_quantity_reported
                                                                           + total_quantity_planned)
                orders_stats[order.pk]["planned"] += total_quantity_planned
                orders_stats[order.pk]["reported"] += total_quantity_reported
                orders_stats[order.pk]["total"] += order_entry.quantity
    if order_id:
        return steps, orders[0], leftovers, orders_stats
    return steps, orders, leftovers, orders_stats


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
