from django.shortcuts import render, render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.urls import reverse
from django.db.models import F
from django.db import connection

from .models import *


def ceil(a, b):
    if a % b == 0:
        return a // b
    else:
        return a // b + 1


def get_basic_info():
    basic_info = {}
    basic_info['blog_name'] = Setting.objects.get(name='blog_name').value
    basic_info['page_size'] = int(Setting.objects.get(name='page_size').value)
    basic_info['meta_page_size'] = int(Setting.objects.get(name='meta_page_size').value)
    basic_info['number_of_category'] = Meta.objects.filter(type='category').count()
    basic_info['number_of_tag'] = Meta.objects.filter(type='tag').count()
    basic_info['number_of_link'] = Link.objects.all().count()
    return basic_info


def get_content_category_list(content_id):
    category_list_query = 'SELECT id, name, slug ' \
                          'FROM blog_meta ' \
                          'WHERE id in (' \
                          'SELECT meta_id_id ' \
                          'FROM blog_relationship ' \
                          'WHERE content_id_id = %s ' \
                          ')' \
                          'AND type = "category";' % content_id

    return Meta.objects.raw(category_list_query)


def get_content_tag_list(tag_id):
    tag_list_query = 'SELECT id, name, slug ' \
                     'FROM blog_meta ' \
                     'WHERE id in (' \
                     'SELECT meta_id_id ' \
                     'FROM blog_relationship ' \
                     'WHERE content_id_id = %s ' \
                     ')' \
                     'AND type = "tag";' % tag_id

    return Meta.objects.raw(tag_list_query)


def index(request, page_id=1):
    basic_info = get_basic_info()
    basic_info['number_of_article'] = Content.objects.filter(type='article').count()
    basic_info['number_of_article_page'] = ceil(basic_info['number_of_article'], basic_info['page_size'])
    if page_id <= 0 or page_id > basic_info['number_of_article_page']:
        raise Http404('Could not found this page!')

    left_range = 0 + basic_info['page_size'] * (page_id - 1)

    article_list_query = 'SELECT * FROM blog_content ' \
                         'WHERE blog_content.type = "article" ' \
                         'ORDER BY blog_content.create_time DESC ' \
                         'LIMIT %s, %s;' % (left_range, basic_info['page_size'])

    article_list = Content.objects.raw(article_list_query)
    page_list = Content.objects.filter(type='page').order_by('priority_id')
    category_list = []
    tag_list = []

    for article_item in article_list:
        raw_category_list = get_content_category_list(article_item.id)
        category_list.append(raw_category_list)
        raw_tag_list = get_content_tag_list(article_item.id)
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


def article(request, article_slug):
    try:
        article_info = Content.objects.get(slug=article_slug)
    except (KeyError, Content.DoesNotExist):
        raise Http404('Could not found this page!')

    basic_info = get_basic_info()

    page_list = Content.objects.filter(type='page').order_by('priority_id')
    category_list = get_content_category_list(article_info.id)
    tag_list = get_content_tag_list(article_info.id)

    context = {
        'page_list': page_list,
        'category_list': category_list,
        'tag_list': tag_list,
        'article_info': article_info,
        'basic_info': basic_info,
    }

    return render(request, 'blog/article.html', context)


def category(request, page_id=1):
    basic_info = get_basic_info()
    basic_info['number_of_category'] = Meta.objects.filter(type='category').count()
    basic_info['number_of_category_page'] = ceil(basic_info['number_of_category'], basic_info['meta_page_size'])
    if page_id <= 0 or page_id > basic_info['number_of_category_page']:
        raise Http404('Could not found this page!')
    left_range = 0 + basic_info['meta_page_size'] * (page_id - 1)

    category_query = '''SELECT blog_meta.id, blog_meta.name, blog_meta.slug, blog_meta.description, COUNT(blog_meta.id)
                        FROM blog_meta, blog_relationship, blog_content 
                        WHERE blog_meta.id = blog_relationship.meta_id_id 
                        AND blog_content.id = blog_relationship.content_id_id
                        AND blog_meta.type = "category"
                        GROUP BY blog_meta.id
                        ORDER BY blog_meta.priority_id
                        LIMIT %s, %s;
    ''' % (left_range, basic_info['meta_page_size'])

    cursor = connection.cursor()
    cursor.execute(category_query)
    category_list = cursor.fetchall()
    page_list = Content.objects.filter(type='page').order_by('priority_id')

    context = {
        'category_list': category_list,
        'page_list': page_list,
        'basic_info': basic_info,
        'page_id': page_id,
    }

    return render(request, 'blog/category.html', context)


def category_detail(request, category_slug, page_id=1):
    category_info = Meta.objects.get(slug=category_slug)
    category_id = category_info.id

    basic_info = get_basic_info()
    basic_info['number_of_article'] = Relationship.objects.filter(meta_id=category_id).count()
    basic_info['number_of_article_page'] = ceil(basic_info['number_of_article'], basic_info['page_size'])
    if page_id <= 0 or page_id > basic_info['number_of_article_page']:
        raise Http404('Could not found this page!')

    left_range = 0 + basic_info['page_size'] * (page_id - 1)
    page_list = Content.objects.filter(type='page').order_by('priority_id')

    article_list_query = '''
                         SELECT *
                         FROM blog_content
                         WHERE blog_content.id in (
                         SELECT content_id_id
                         FROM blog_relationship
                         WHERE meta_id_id = %s
                         )
                         AND blog_content.type = "article"
                         ORDER BY blog_content.create_time DESC
                         LIMIT %s, %s;
    ''' % (category_id, left_range, basic_info['page_size'])

    article_list = Content.objects.raw(article_list_query)
    category_list = []
    tag_list = []

    for article_item in article_list:
        raw_category_list = get_content_category_list(article_item.id)
        category_list.append(raw_category_list)
        raw_tag_list = get_content_tag_list(article_item.id)
        tag_list.append(raw_tag_list)

    context = {
        'article_list': article_list,
        'category_list': category_list,
        'page_list': page_list,
        'tag_list': tag_list,
        'basic_info': basic_info,
        'page_id': page_id,
        'category_info': category_info,
    }

    return render(request, 'blog/category_detail.html', context)


def tag(request, page_id=1):
    basic_info = get_basic_info()
    basic_info['number_of_tag'] = Meta.objects.filter(type='tag').count()
    basic_info['number_of_tag_page'] = ceil(basic_info['number_of_tag'], basic_info['meta_page_size'])
    if page_id <= 0 or page_id > basic_info['number_of_tag_page']:
        raise Http404('Could not found this page!')
    left_range = 0 + basic_info['meta_page_size'] * (page_id - 1)

    tag_query = '''SELECT blog_meta.id, blog_meta.name, blog_meta.slug, blog_meta.description, COUNT(blog_meta.id)
                   FROM blog_meta, blog_relationship, blog_content 
                   WHERE blog_meta.id = blog_relationship.meta_id_id 
                   AND blog_content.id = blog_relationship.content_id_id
                   AND blog_meta.type = "tag"
                   GROUP BY blog_meta.id
                   ORDER BY blog_meta.priority_id
                   LIMIT %s, %s;
    ''' % (left_range, basic_info['meta_page_size'])

    cursor = connection.cursor()
    cursor.execute(tag_query)
    tag_list = cursor.fetchall()
    page_list = Content.objects.filter(type='page').order_by('priority_id')

    context = {
        'tag_list': tag_list,
        'page_list': page_list,
        'basic_info': basic_info,
        'page_id': page_id,
    }

    return render(request, 'blog/tag.html', context)


def tag_detail(request, tag_slug, page_id=1):
    tag_info = Meta.objects.get(slug=tag_slug)
    tag_id = tag_info.id

    basic_info = get_basic_info()
    basic_info['number_of_article'] = Relationship.objects.filter(meta_id=tag_id).count()
    basic_info['number_of_article_page'] = ceil(basic_info['number_of_article'], basic_info['page_size'])
    if page_id <= 0 or page_id > basic_info['number_of_article_page']:
        raise Http404('Could not found this page!')

    left_range = 0 + basic_info['page_size'] * (page_id - 1)
    page_list = Content.objects.filter(type='page').order_by('priority_id')

    article_list_query = '''
                         SELECT *
                         FROM blog_content
                         WHERE blog_content.id in (
                         SELECT content_id_id
                         FROM blog_relationship
                         WHERE meta_id_id = %s
                         )
                         AND blog_content.type = "article"
                         ORDER BY blog_content.create_time DESC
                         LIMIT %s, %s;
    ''' % (tag_id, left_range, basic_info['page_size'])

    article_list = Content.objects.raw(article_list_query)
    category_list = []
    tag_list = []

    for article_item in article_list:
        raw_category_list = get_content_category_list(article_item.id)
        category_list.append(raw_category_list)
        raw_tag_list = get_content_tag_list(article_item.id)
        tag_list.append(raw_tag_list)

    context = {
        'article_list': article_list,
        'category_list': category_list,
        'page_list': page_list,
        'tag_list': tag_list,
        'basic_info': basic_info,
        'page_id': page_id,
        'tag_info': tag_info,
    }

    return render(request, 'blog/tag_detail.html', context)


def link(request, page_id=1):
    basic_info = get_basic_info()
    basic_info['number_of_link'] = Link.objects.filter().count()
    basic_info['number_of_link_page'] = ceil(basic_info['number_of_link'], basic_info['meta_page_size'])
    if page_id <= 0 or page_id > basic_info['number_of_link_page']:
        raise Http404('Could not found this page!')
    left_range = 0 + basic_info['meta_page_size'] * (page_id - 1)

    link_list_query = '''
                      SELECT *
                      FROM blog_link
                      LIMIT %s, %s;
    ''' % (left_range, basic_info['meta_page_size'])

    link_list = Link.objects.raw(link_list_query)
    page_list = Content.objects.filter(type='page').order_by('priority_id')

    context = {
        'link_list': link_list,
        'page_list': page_list,
        'basic_info': basic_info,
        'page_id': page_id,
    }

    return render(request, 'blog/link.html', context)


def archive(request):
    basic_info = get_basic_info()

    archive_list_query = '''
                         SELECT DISTINCT YEAR(create_time) AS create_year,
                         MONTH(create_time) AS create_month,
                         COUNT(*) number_of_content
                         FROM blog_content
                         WHERE type = "article"
                         GROUP BY create_year, create_month
                         ORDER BY create_year, create_month DESC;
    '''

    cursor = connection.cursor()
    cursor.execute(archive_list_query)
    archive_list = cursor.fetchall()
    page_list = Content.objects.filter(type='page').order_by('priority_id')

    context = {
        'basic_info': basic_info,
        'archive_list': archive_list,
        'page_list': page_list,
    }

    return render(request, 'blog/archive.html', context)


def archive_detail(request, year, month, page_id=1):
    basic_info = get_basic_info()
    if int(month) <= 9:
        time_format = '%s-0%s' % (year, month)
    else:
        time_format = '%s-%s' % (year, month)
    basic_info['number_of_article'] = Content.objects.filter(create_time__startswith=time_format, type='article').count()
    basic_info['number_of_article_page'] = ceil(basic_info['number_of_article'], basic_info['page_size'])
    if page_id <= 0 or page_id > basic_info['number_of_article_page']:
        raise Http404('Could not found this page!')

    left_range = 0 + basic_info['page_size'] * (page_id - 1)
    page_list = Content.objects.filter(type='page').order_by('priority_id')

    article_list_query = '''
                         SELECT *
                         FROM blog_content
                         WHERE create_time
                         LIKE "%s%%%%"
                         AND type = "article"
                         ORDER BY create_time DESC
                         LIMIT %s, %s;
    ''' % (time_format, left_range, basic_info['page_size'])

    print(article_list_query)

    article_list = Content.objects.raw(article_list_query)
    category_list = []
    tag_list = []

    for article_item in article_list:
        raw_category_list = get_content_category_list(article_item.id)
        category_list.append(raw_category_list)
        raw_tag_list = get_content_tag_list(article_item.id)
        tag_list.append(raw_tag_list)

    context = {
        'article_list': article_list,
        'category_list': category_list,
        'page_list': page_list,
        'tag_list': tag_list,
        'basic_info': basic_info,
        'page_id': page_id,
        'year': year,
        'month': month,
    }

    return render(request, 'blog/archive_detail.html', context)


def search(request, page_id=1):
    keyword = request.GET['keyword']
    basic_info = get_basic_info()
    basic_info['number_of_article'] = Content.objects.filter(type='article', title__icontains=keyword).count()
    basic_info['number_of_article_page'] = ceil(basic_info['number_of_article'], basic_info['page_size'])
    # if page_id <= 0 or page_id > basic_info['number_of_article_page']:
    #     raise Http404('Could not found this page!')

    left_range = 0 + basic_info['page_size'] * (page_id - 1)

    article_list_query = 'SELECT * FROM blog_content ' \
                         'WHERE blog_content.type = "article" ' \
                         'AND blog_content.title ' \
                         'LIKE "%%%%%s%%%%" ' \
                         'ORDER BY blog_content.create_time DESC ' \
                         'LIMIT %s, %s;' % (keyword, left_range, basic_info['page_size'])

    article_list = Content.objects.raw(article_list_query)
    page_list = Content.objects.filter(type='page').order_by('priority_id')
    category_list = []
    tag_list = []

    for article_item in article_list:
        raw_category_list = get_content_category_list(article_item.id)
        category_list.append(raw_category_list)
        raw_tag_list = get_content_tag_list(article_item.id)
        tag_list.append(raw_tag_list)

    context = {
        'article_list': article_list,
        'category_list': category_list,
        'page_list': page_list,
        'tag_list': tag_list,
        'basic_info': basic_info,
        'page_id': page_id,
        'keyword': keyword,
    }

    return render(request, 'blog/search.html', context)
