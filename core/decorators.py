import json
from functools import wraps

from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect
from django.template.loader import render_to_string


def unauthenticated_user(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return view_func(request, *args, **kwargs)
        else:
            return redirect("home")

    return _wrapped_view


def allowed_user_roles(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated and request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            else:
                return HttpResponseForbidden("You don't have permission to access this page.")

        return _wrapped_view

    return decorator


def toast_message(success_message=None, error_message=None):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                response = view_func(request, *args, **kwargs)

                toast_data = getattr(response, "toast_data", {})

                if success_message:
                    formatted_success_message = success_message.format(**toast_data)

                    toast_html = render_to_string(
                        "core/partials/toast.html", {"message": formatted_success_message, "toast_class": "bg-success"}
                    )

                    if isinstance(response, HttpResponse):
                        response["HX-Trigger"] = json.dumps({"toast-loaded": {"toast": toast_html}})
                    else:
                        response = HttpResponse(response)
                        response["HX-Trigger"] = json.dumps({"toast-loaded": {"toast": toast_html}})

                return response

            except Exception as e:
                formatted_error_message = error_message.format(**toast_data) if error_message else str(e)

                toast_html = render_to_string(
                    "core/partials/toast.html", {"message": formatted_error_message, "toast_class": "bg-danger"}
                )

                response = HttpResponse(status=500)
                response["HX-Trigger"] = json.dumps({"toast-loaded": {"toast": toast_html}})
                return response

        return wrapper

    return decorator
