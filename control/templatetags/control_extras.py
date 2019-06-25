from django import template

from blog.models import User


register = template.Library()


@register.simple_tag
def get_element_from_index(source_list, index):
    return source_list[index]


@register.simple_tag
def get_view_name(source_str, pos):
    str_list = source_str.split('/')
    print(str_list[pos])
    return str_list[pos]


@register.simple_tag
def str_cat(a, b):
    return a + b


@register.simple_tag
def get_user_nickname_by_id(user_id):
    return User.objects.get(id=user_id).nickname


@register.simple_tag
def get_user_group_by_id(user_id):
    return User.objects.get(id=user_id).group


@register.simple_tag
def get_user_username_by_id(user_id):
    return User.objects.get(id=user_id).username


@register.simple_tag
def str_to_int(source):
    return int(source)
