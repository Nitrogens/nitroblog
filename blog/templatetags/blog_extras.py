from django import template


register = template.Library()


@register.simple_tag
def get_element_from_index(source_list, index):
    return source_list[index]


@register.simple_tag
def get_view_name(source_str):
    str_list = source_str.split('/')
    return str_list[1]


@register.simple_tag
def str_cat(a, b):
    return a + b
