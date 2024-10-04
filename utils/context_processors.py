from django.conf import settings


def debug_context_processor(request):
    return {"debug": settings.DEBUG}
