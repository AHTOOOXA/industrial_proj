from django.template.defaultfilters import register


@register.filter(name='lookup')
def lookup(dictionary, key):
    return dictionary.get(key)
