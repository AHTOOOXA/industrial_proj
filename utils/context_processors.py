from django.conf import settings

from core.models import Table


def debug_context_processor(request):
    return {"debug": settings.DEBUG}


def active_step_pk_context_processor(request):
    return {"active_step_pk": Table.objects.first().current_step.pk}
