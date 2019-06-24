from django.shortcuts import render, render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.urls import reverse
from django.db.models import F
from django.db import connection, ProgrammingError, IntegrityError

import markdown, pypandoc, datetime

from .models import *
from .forms import *
from .common import *


def get_basic_info(request):
    basic_info = {}

    if request.session.get('is_login') is None:
        basic_info['is_login'] = False
    else:
        basic_info['is_login'] = True
        user_info = User.objects.get(id=int(request.session['user_id']))
        basic_info['user_nickname'] = user_info.nickname
        basic_info['user_email'] = user_info.mail

    basic_info['blog_name'] = Setting.objects.get(name='blog_name').value
    basic_info['page_size'] = int(Setting.objects.get(name='page_size').value)
    basic_info['meta_page_size'] = int(Setting.objects.get(name='meta_page_size').value)
    basic_info['number_of_category'] = Meta.objects.filter(type='category').count()
    basic_info['number_of_tag'] = Meta.objects.filter(type='tag').count()
    basic_info['number_of_link'] = Link.objects.all().count()
    basic_info['github'] = Setting.objects.get(name='github').value
    basic_info['weibo'] = Setting.objects.get(name='weibo').value
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


def login(request):
    if request.session.get('is_login', None):
        return HttpResponseRedirect(reverse('blog:index', args=()))

    login_message = None

    if request.method == 'POST':
        form_info = LoginForm(request.POST)
        if form_info.is_valid():
            username = form_info.cleaned_data['username']
            password = form_info.cleaned_data['password']
            try:
                user = User.objects.get(username=username)
                if password_encrypt(password) == user.password:
                    request.session['is_login'] = True
                    request.session['username'] = user.username
                    request.session['user_group'] = user.group
                    request.session['user_id'] = user.id
                    user.last_login_time = datetime.datetime.now()
                    user.save()
                    return HttpResponseRedirect(reverse('blog:index', args=()))
                else:
                    login_message = '用户名或密码错误！'
            except User.DoesNotExist:
                login_message = '用户名或密码错误！'
        else:
            login_message = '请检查输入格式！'

    form_info = LoginForm()
    return render(request, 'blog/login.html', locals())


def logout(request):
    if not request.session.get('is_login', None):
        return HttpResponseRedirect(reverse('blog:index', args=()))

    request.session.flush()

    return HttpResponseRedirect(reverse('blog:index', args=()))


def register(request):
    if request.session.get('is_login') is not None:
        return HttpResponseRedirect(reverse('blog:index', args=()))

    basic_info = get_basic_info(request)
    response_message = ''

    if request.method == 'POST':
        form_info = RegisterForm(request.POST)
        if form_info.is_valid():
            if request.POST['password'] == request.POST['password_confirm']:
                password = password_encrypt(request.POST['password_confirm'])
                operation_query = '''
                    INSERT INTO blog_user
                    VALUES (NULL, '%s', '%s', '%s', '%s', '%s', NOW(), NOW(), 'user');
                    ''' % (request.POST['username'], password, request.POST['email'],
                           request.POST['url'], request.POST['nickname'])
                try:
                    cursor = connection.cursor()
                    cursor.execute(operation_query)
                    return HttpResponseRedirect(reverse('blog:index', args=()))
                except ProgrammingError:
                    response_message = '注册失败！'
                    return render(request, 'blog/register.html', locals())
                except IntegrityError:
                    response_message = '用户名已经存在！'
                    return render(request, 'blog/register.html', locals())
            else:
                response_message = '密码输入不一致！'
                return render(request, 'blog/register.html', locals())
        else:
            response_message = '请检查输入格式！'
            return render(request, 'blog/register.html', locals())

    form_info = RegisterForm()
    return render(request, 'blog/register.html', locals())


def index(request, page_id=1):
    basic_info = get_basic_info(request)
    basic_info['number_of_article'] = Content.objects.filter(type='article').count()
    basic_info['number_of_article_page'] = ceil(basic_info['number_of_article'], basic_info['page_size'])

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
        article_item.summary = pypandoc.convert(article_item.summary, 'html', format='md')
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

    response_message = ''

    if request.method == 'POST':
        if request.session.get('is_login') is None:
            return HttpResponseRedirect(reverse('blog:login', args=()))

        if int(request.POST['id']) != 0:
            try:
                comment_info = Comment.objects.get(id=int(request.POST['id']))
            except (KeyError, Content.DoesNotExist):
                return HttpResponseRedirect(reverse('blog:article', args=article_slug))

        if request.META.get('HTTP_X_FORWARDED_FOR') is not None:
            ip = request.META['HTTP_X_FORWARDED_FOR']
        else:
            ip = request.META['REMOTE_ADDR']

        if int(request.POST['id']) == 0:
            comment_id = 'NULL'
        else:
            comment_id = int(request.POST['id'])

        comment_commit_query = '''
        INSERT INTO blog_comment
        VALUES (NULL, '%s', '%s', '%s', 'rejected', '%s', %s, %s, %s);
        ''' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ip, request.POST['text'], request.session['user_id'], article_info.id, comment_id)

        try:
            cursor = connection.cursor()
            cursor.execute(comment_commit_query)
        except ProgrammingError:
            response_message = '操作失败！'
            cursor = connection.cursor()

    basic_info = get_basic_info(request)

    page_list = Content.objects.filter(type='page').order_by('priority_id')
    category_list = get_content_category_list(article_info.id)
    tag_list = get_content_tag_list(article_info.id)

    article_info.text = pypandoc.convert(article_info.text, 'html5', format='md', extra_args=['--mathjax',
             '--smart', '--no-highlight'])

    comment_commit_form_info = CommentCreateForm()

    return render(request, 'blog/article.html', locals())


def category(request, page_id=1):
    basic_info = get_basic_info(request)
    basic_info['number_of_category'] = Meta.objects.filter(type='category').count()
    basic_info['number_of_category_page'] = ceil(basic_info['number_of_category'], basic_info['meta_page_size'])
    left_range = 0 + basic_info['meta_page_size'] * (page_id - 1)

    category_query = '''SELECT blog_meta.id, blog_meta.name, blog_meta.slug, blog_meta.description, COUNT(blog_content.id)
                        FROM blog_meta LEFT OUTER JOIN (blog_content, blog_relationship) ON (blog_meta.id = blog_relationship.meta_id_id
                        AND blog_content.id = blog_relationship.content_id_id)
                        WHERE blog_meta.type = "category"
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

    basic_info = get_basic_info(request)
    basic_info['number_of_article'] = Relationship.objects.filter(meta_id=category_id).count()
    basic_info['number_of_article_page'] = ceil(basic_info['number_of_article'], basic_info['page_size'])

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
        article_item.summary = pypandoc.convert(article_item.summary, 'html', format='md')
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
    basic_info = get_basic_info(request)
    basic_info['number_of_tag'] = Meta.objects.filter(type='tag').count()
    basic_info['number_of_tag_page'] = ceil(basic_info['number_of_tag'], basic_info['meta_page_size'])
    left_range = 0 + basic_info['meta_page_size'] * (page_id - 1)

    tag_query = '''
    SELECT blog_meta.id, blog_meta.name, blog_meta.slug, blog_meta.description, COUNT(blog_content.id)
    FROM blog_meta LEFT OUTER JOIN (blog_content, blog_relationship) ON (blog_meta.id = blog_relationship.meta_id_id
    AND blog_content.id = blog_relationship.content_id_id)
    WHERE blog_meta.type = "tag"
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

    basic_info = get_basic_info(request)
    basic_info['number_of_article'] = Relationship.objects.filter(meta_id=tag_id).count()
    basic_info['number_of_article_page'] = ceil(basic_info['number_of_article'], basic_info['page_size'])

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
        article_item.summary = pypandoc.convert(article_item.summary, 'html', format='md')
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
    basic_info = get_basic_info(request)
    basic_info['number_of_link'] = Link.objects.filter().count()
    basic_info['number_of_link_page'] = ceil(basic_info['number_of_link'], basic_info['meta_page_size'])
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
    basic_info = get_basic_info(request)

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
    basic_info = get_basic_info(request)
    if int(month) <= 9:
        time_format = '%s-0%s' % (year, month)
    else:
        time_format = '%s-%s' % (year, month)
    basic_info['number_of_article'] = Content.objects.filter(create_time__startswith=time_format, type='article').count()
    basic_info['number_of_article_page'] = ceil(basic_info['number_of_article'], basic_info['page_size'])

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
        article_item.summary = pypandoc.convert(article_item.summary, 'html', format='md')
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
    basic_info = get_basic_info(request)
    basic_info['number_of_article'] = Content.objects.filter(type='article', title__icontains=keyword).count()
    basic_info['number_of_article_page'] = ceil(basic_info['number_of_article'], basic_info['page_size'])

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
        article_item.summary = pypandoc.convert(article_item.summary, 'html', format='md')
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
