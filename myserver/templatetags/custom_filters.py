from django import template

register = template.Library()

@register.filter
def get_extra_image(book, index):
    attr = f"extra_image_{index}"
    return getattr(book, attr, None)
