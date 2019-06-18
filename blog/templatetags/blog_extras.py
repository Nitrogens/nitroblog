from django import template


register = template.Library()


@register.simple_tag
def get_element_from_index(source_list, index):
    return source_list[index]