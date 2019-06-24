from django import template

from blog.models import User

import urllib, hashlib


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
def get_gravatar(email):
    gravatar_url = "https://www.gravatar.com/avatar/" + hashlib.md5(email.lower().encode()).hexdigest() + "?s=200"
    return gravatar_url

