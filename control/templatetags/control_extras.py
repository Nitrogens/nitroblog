from django import template

from blog.models import User


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


@register.simple_tag
def get_user_nickname_by_id(user_id):
    return User.objects.get(id=user_id).nickname


@register.simple_tag
def str_to_int(source):
    return int(source)
