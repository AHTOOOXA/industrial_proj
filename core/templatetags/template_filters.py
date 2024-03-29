from django.template.defaultfilters import register


@register.filter(name="lookup")
def lookup(dictionary, key):
    return dictionary.get(key)


@register.filter(name="has_role")
def has_role(user, role_name):
    return user.role == role_name


@register.filter(name="get_detail_class")
def get_detail_class(detail):
    if detail:
        return f"detail-{detail.pk}"
    else:
        return ""
