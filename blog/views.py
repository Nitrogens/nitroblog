from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.urls import reverse
from django.db.models import F

from .models import *


def ceil(a, b):
    if a % b == 0:
        return a // b
    else:
        return a // b + 1


def get_basic_info():
    basic_info = {}
    basic_info['blog_name'] = Setting.objects.filter(name='blog_name')[0].value
    basic_info['page_size'] = int(Setting.objects.filter(name='page_size')[0].value)
    basic_info['number_of_category'] = Meta.objects.filter(type='category').count()
    basic_info['number_of_tag'] = Meta.objects.filter(type='tag').count()
    basic_info['number_of_link'] = Link.objects.all().count()
    basic_info['number_of_article'] = Content.objects.filter(type='article').count()
    basic_info['number_of_page'] = ceil(basic_info['number_of_article'], basic_info['page_size'])
    return basic_info


def index(request, page_id=1):

    article_list_query = 'SELECT * FROM blog_content ' \
            'WHERE blog_content.type = "article" ' \
            'ORDER BY blog_content.create_time DESC ' \
            'LIMIT %s, %s;'

    basic_info = get_basic_info()
    if page_id <= 0 or page_id > basic_info['number_of_page']:
        raise Http404('Could not found this page!')

    left_range = 0 + basic_info['page_size'] * (page_id - 1)
    article_list = Content.objects.raw(article_list_query, [left_range, basic_info['page_size']])
    page_list = Content.objects.filter(type='page').order_by('priority_id')
    category_list = []
    tag_list = []

    for article in article_list:
        category_list_query = 'SELECT id, name, slug ' \
                              'FROM blog_meta ' \
                              'WHERE id in (' \
                              'SELECT meta_id_id ' \
                              'FROM blog_relationship ' \
                              'WHERE content_id_id = %s ' \
                              ')' \
                              'AND type = "category";'
        raw_category_list = Meta.objects.raw(category_list_query, [article.id])
        category_list.append(raw_category_list)

        tag_list_query = 'SELECT id, name, slug ' \
                         'FROM blog_meta ' \
                         'WHERE id in (' \
                         'SELECT meta_id_id ' \
                         'FROM blog_relationship ' \
                         'WHERE content_id_id = %s ' \
                         ')' \
                         'AND type = "tag";'
        raw_tag_list = Meta.objects.raw(tag_list_query, [article.id])
        tag_list.append(raw_tag_list)

    context = {
        'article_list': article_list,
        'category_list': category_list,
        'page_list': page_list,
        'tag_list': tag_list,
        'basic_info': basic_info,
        'page_id': page_id,
    }

    return render(request, 'blog/index.html', context)

