from django.shortcuts import render, render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.urls import reverse
from django.db.models import F
from django.db import connection, ProgrammingError, IntegrityError
import hashlib, base64, datetime


from blog.common import *
from blog.models import *
from blog.views import get_basic_info, get_content_category_list
from .forms import *


def login(request):
    if request.session.get('is_login', None):
        return HttpResponseRedirect(reverse('control:dashboard', args=()))

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
                    request.session['user_id'] = user.id
                    user.last_login_time = datetime.datetime.now()
                    user.save()
                    return HttpResponseRedirect(reverse('control:dashboard', args=()))
                else:
                    login_message = '用户名或密码错误！'
            except User.DoesNotExist:
                login_message = '用户名或密码错误！'
        else:
            login_message = '请检查输入格式！'

    form_info = LoginForm()
    return render(request, 'control/login.html', locals())


def logout(request):
    if not request.session.get('is_login', None):
        return HttpResponseRedirect(reverse('control:login', args=()))

    request.session.flush()

    return HttpResponseRedirect(reverse('control:login', args=()))


def forbidden(request):
    if request.session.get('is_login') is None:
        return HttpResponseRedirect(reverse('control:login', args=()))

    return render(request, 'control/forbidden.html', locals())


def dashboard(request):
    if request.session.get('is_login') is None:
        return HttpResponseRedirect(reverse('control:login', args=()))

    number = {
        'article': Content.objects.filter(type='article').count(),
        'comment': Comment.objects.all().count(),
        'category': Meta.objects.filter(type='category').count(),
        'tag': Meta.objects.filter(type='tag').count(),
    }

    recent_article_list_query = '''
    SELECT title, slug, id
    FROM blog_content
    WHERE type = 'article'
    ORDER BY create_time DESC
    LIMIT 0, 10;
    '''

    recent_comment_list_query = '''
    SELECT blog_comment.text, blog_user.username
    FROM blog_comment, blog_user
    WHERE blog_comment.author_id_id = blog_user.id
    ORDER BY blog_comment.create_time DESC
    LIMIT 0, 10;
    '''

    cursor = connection.cursor()
    cursor.execute(recent_article_list_query)
    recent_article_list = cursor.fetchall()
    cursor.execute(recent_comment_list_query)
    recent_comment_list = cursor.fetchall()

    context = {
        'number': number,
        'recent_article_list': recent_article_list,
        'recent_comment_list': recent_comment_list,
    }

    return render(request, 'control/general/dashboard.html', context)


def personal_information(request):
    if request.session.get('is_login') is None:
        return HttpResponseRedirect(reverse('control:login', args=()))

    response_message = ''

    if request.method == 'POST':
        form_info = PersonalInformationForm(request.POST)
        if form_info.is_valid():
            operation_query = '''
            UPDATE blog_user
            SET mail = '%s',
            url = '%s',
            nickname = '%s'
            WHERE username = '%s';
            ''' % (form_info.cleaned_data['email'], form_info.cleaned_data['url'], form_info.cleaned_data['nickname'], User.objects.get(id=request.session['user_id']).username)
            try:
                cursor = connection.cursor()
                cursor.execute(operation_query)
                response_message = '更新成功！'
            except ProgrammingError:
                response_message = '更新失败！'
        else:
            response_message = '请检查输入格式！'

    user_info = User.objects.get(username=User.objects.get(id=request.session['user_id']).username)
    form_info = PersonalInformationForm()
    form_info['email'].initial = user_info.mail
    form_info['url'].initial = user_info.url
    form_info['nickname'].initial = user_info.nickname
    return render(request, 'control/general/personal_information.html', locals())


def change_password(request):
    if request.session.get('is_login') is None:
        return HttpResponseRedirect(reverse('control:login', args=()))

    response_message = ''

    if request.method == 'POST':
        form_info = PasswordChangeForm(request.POST)
        if form_info.is_valid():
            user = User.objects.get(username=User.objects.get(id=request.session['user_id']).username)
            if user.password == password_encrypt(form_info.cleaned_data['current_password']) and form_info.cleaned_data['new_password'] == form_info.cleaned_data['new_password_confirm']:
                try:
                    user.password = password_encrypt(form_info.cleaned_data['new_password'])
                    user.save()
                    response_message = '修改成功！'
                except (ProgrammingError, NameError):
                    response_message = '修改失败！'
            else:
                response_message = '密码输入错误！'
        else:
            response_message = '请检查输入格式！'

    form_info = PasswordChangeForm()
    return render(request, 'control/general/change_password.html', locals())


def article_list(request, page_id=1):
    if request.session.get('is_login') is None:
        return HttpResponseRedirect(reverse('control:login', args=()))

    if User.objects.get(id=request.session['user_id']).group != 'administrator' and User.objects.get(id=request.session['user_id']).group != 'writer':
        return HttpResponseRedirect(reverse('control:forbidden', args=()))

    response_message = ''

    if request.method == 'POST':
        article_id_list = request.POST.getlist('article_cid[]')
        article_id_set = ''
        if article_id_list:
            flag = 0
            for article_id in article_id_list:
                if flag > 0:
                    article_id_set += ', '
                article_id_set += article_id
                flag += 1
            operation_query = '''
            SELECT * FROM blog_content
            WHERE id in (%s) 
            ''' % article_id_set
            if User.objects.get(id=request.session['user_id']).group != 'administrator':
                operation_query += '''
                AND author_id_id = %s
                ''' % request.session['user_id']

            try:
                article_list = Content.objects.raw(operation_query)
                for article in article_list:
                    article.delete()
            except (NameError, ProgrammingError):
                response_message = '删除失败！'

    keyword = request.GET.get('keyword')
    category_id = request.GET.get('category')

    if keyword is None:
        keyword = ''
    if category_id is None:
        category_id = 0
    else:
        category_id = int(category_id)

    page_size = 10
    basic_info = get_basic_info(request)
    basic_info['number_of_article'] = 0

    number_of_article_query = '''
    SELECT COUNT(id)
    FROM blog_content
    WHERE type = 'article'
    '''

    if User.objects.get(id=request.session['user_id']).group == 'writer':
        number_of_article_query += '''
        AND author_id_id = %s
        ''' % request.session['user_id']

    if keyword != '':
        number_of_article_query += '''
        AND title LIKE '%%%%%s%%%%'
        ''' % keyword

    if category_id != 0:
        number_of_article_query += '''
        AND id in (
            SELECT content_id_id
            FROM blog_relationship
            WHERE meta_id_id = %s
        )
        ''' % category_id

    cursor = connection.cursor()
    cursor.execute(number_of_article_query)
    basic_info['number_of_article'] = cursor.fetchone()[0]
    basic_info['number_of_article_page'] = ceil(basic_info['number_of_article'], page_size)

    left_range = 0 + page_size * (page_id - 1)

    article_list_query = '''
    SELECT blog_content.id, blog_content.title, blog_content.edit_time, 
    COUNT(blog_comment.content_id_id), blog_content.slug, blog_content.author_id_id
    FROM blog_content LEFT OUTER JOIN blog_comment
    ON (blog_content.id = blog_comment.content_id_id)
    WHERE blog_content.type = 'article' 
    '''

    if User.objects.get(id=request.session['user_id']).group != 'administrator':
        article_list_query += '''
        AND blog_content.author_id_id = %s
        ''' % request.session['user_id']

    if keyword != '':
        article_list_query += '''
        AND blog_content.title LIKE '%%%%%s%%%%'
        ''' % keyword

    if category_id != 0:
        article_list_query += '''
        AND blog_content.id in (
            SELECT content_id_id
            FROM blog_relationship
            WHERE meta_id_id = %s
        )
        ''' % category_id

    article_list_query += '''
    GROUP BY blog_content.id
    ORDER BY blog_content.edit_time DESC
    LIMIT %s, %s;
    ''' % (left_range, page_size)

    cursor = connection.cursor()
    cursor.execute(article_list_query)
    article_list = cursor.fetchall()
    category_list_of_content = []

    for article_item in article_list:
        raw_category_list = get_content_category_list(article_item[0])
        category_list_of_content.append(raw_category_list)

    form_info = ArticleFilterForm({'keyword': keyword, 'category': category_id,})

    return render(request, 'control/manage/article_list.html', locals())


def page_list(request, page_id=1):
    if request.session.get('is_login') is None:
        return HttpResponseRedirect(reverse('control:login', args=()))

    if User.objects.get(id=request.session['user_id']).group != 'administrator' and User.objects.get(id=request.session['user_id']).group != 'writer':
        return HttpResponseRedirect(reverse('control:forbidden', args=()))

    if request.method == 'POST':
        article_id_list = request.POST.getlist('article_cid[]')
        article_id_set = ''
        if article_id_list:
            flag = 0
            for article_id in article_id_list:
                if flag > 0:
                    article_id_set += ', '
                article_id_set += article_id
                flag += 1
            operation_query = '''
            SELECT * FROM blog_content
            WHERE id in (%s) 
            ''' % article_id_set
            if User.objects.get(id=request.session['user_id']).group != 'administrator':
                operation_query += '''
                AND author_id_id = %s
                ''' % request.session['user_id']

            try:
                article_list = Content.objects.raw(operation_query)
                for article in article_list:
                    article.delete()
            except (KeyError, Content.DoesNotExist):
                response_message = '删除失败！'

    keyword = request.GET.get('keyword')

    if keyword is None:
        keyword = ''

    page_size = 10
    basic_info = get_basic_info(request)

    number_of_article_query = '''
        SELECT COUNT(id)
        FROM blog_content
        WHERE type = 'page'
        '''

    if User.objects.get(id=request.session['user_id']).group == 'writer':
        number_of_article_query += '''
            AND author_id_id = %s
            ''' % request.session['user_id']

    if keyword != '':
        number_of_article_query += '''
            AND title LIKE '%%%%%s%%%%'
            ''' % keyword

    cursor = connection.cursor()
    cursor.execute(number_of_article_query)
    basic_info['number_of_article'] = cursor.fetchone()[0]
    basic_info['number_of_article_page'] = ceil(basic_info['number_of_article'], page_size)

    left_range = 0 + page_size * (page_id - 1)

    article_list_query = '''
    SELECT blog_content.id, blog_content.title, blog_content.edit_time, 
    COUNT(blog_comment.content_id_id), blog_content.slug, blog_content.author_id_id
    FROM blog_content LEFT OUTER JOIN blog_comment
    ON (blog_content.id = blog_comment.content_id_id)
    WHERE blog_content.type = 'page' 
    '''

    if User.objects.get(id=request.session['user_id']).group != 'administrator':
        article_list_query += '''
        AND blog_content.author_id_id = %s
        ''' % request.session['user_id']

    if keyword != '':
        article_list_query += '''
        AND blog_content.title LIKE '%%%%%s%%%%'
        ''' % keyword

    article_list_query += '''
    GROUP BY blog_content.id
    ORDER BY blog_content.edit_time DESC
    LIMIT %s, %s;
    ''' % (left_range, page_size)

    cursor = connection.cursor()
    cursor.execute(article_list_query)
    article_list = cursor.fetchall()

    form_info = ArticleFilterForm({'keyword': keyword,})

    return render(request, 'control/manage/page_list.html', locals())


def article_create(request):
    if request.session.get('is_login') is None:
        return HttpResponseRedirect(reverse('control:login', args=()))

    if User.objects.get(id=request.session['user_id']).group != 'administrator' and User.objects.get(id=request.session['user_id']).group != 'writer':
        return HttpResponseRedirect(reverse('control:forbidden', args=()))

    response_message = ''

    if request.method == 'POST':
        form_info = ArticleCreateForm(request.POST)
        if form_info.is_valid():
            try:
                cursor = connection.cursor()
                cursor.execute('BEGIN;')
            except ProgrammingError:
                response_message = '操作失败！'
                return render(request, 'control/manage/article_create.html', locals())

            insert_query = '''
            INSERT INTO blog_content
            VALUES (NULL, '%s', '%s', NOW(), NOW(), '%s', '%s', 0, 'article', %s);
            ''' % (request.POST['title'], request.POST['slug'],
                   content_operation(request.POST['summary']), content_operation(request.POST['text']), request.session['user_id'])

            try:
                cursor = connection.cursor()
                cursor.execute(insert_query)
            except IntegrityError:
                response_message = '标识符已被占用！'
                cursor = connection.cursor()
                cursor.execute('ROLLBACK;')
                return render(request, 'control/manage/article_create.html', locals())
            except ProgrammingError:
                response_message = '操作失败！'
                cursor = connection.cursor()
                return render(request, 'control/manage/article_create.html', locals())

            article_id = Content.objects.get(slug=request.POST['slug']).id

            category_id_list = request.POST.getlist('category')
            tag_id_list = request.POST.getlist('tag')
            meta_id_list = category_id_list + tag_id_list

            if meta_id_list:
                meta_id_set = ''
                flag = 0
                for meta_id in meta_id_list:
                    if flag > 0:
                        meta_id_set += ', '
                    meta_id_set += ('(NULL, ' + str(article_id) + ', ' + str(meta_id) + ')')
                    flag += 1
                meta_insert_query = '''
                INSERT INTO blog_relationship
                VALUES %s;
                ''' % meta_id_set
                try:
                    cursor = connection.cursor()
                    cursor.execute(meta_insert_query)
                except ProgrammingError:
                    response_message = '操作失败！'
                    cursor = connection.cursor()
                    cursor.execute('ROLLBACK;')
                    return render(request, 'control/manage/article_create.html', locals())

            try:
                cursor = connection.cursor()
                cursor.execute('COMMIT;')
                return HttpResponseRedirect(reverse('control:article_list', args=()))
            except ProgrammingError:
                response_message = '操作失败！'
                return render(request, 'control/manage/article_create.html', locals())

        else:
            response_message = '请检查输入格式！'
            return render(request, 'control/manage/article_create.html', locals())

    form_info = ArticleCreateForm()
    return render(request, 'control/manage/article_create.html', locals())


def article_edit(request, article_id):
    if request.session.get('is_login') is None:
        return HttpResponseRedirect(reverse('control:login', args=()))

    if User.objects.get(id=request.session['user_id']).group != 'administrator' and User.objects.get(id=request.session['user_id']).group != 'writer':
        return HttpResponseRedirect(reverse('control:forbidden', args=()))

    article_info = None

    try:
        article_info = Content.objects.get(id=article_id, type='article')
    except (KeyError, Content.DoesNotExist):
        return HttpResponseRedirect(reverse('control:forbidden', args=()))

    if User.objects.get(id=request.session['user_id']).group == 'writer' and article_info.author_id.id != request.session['user_id']:
        return HttpResponseRedirect(reverse('control:forbidden', args=()))

    response_message = ''

    if request.method == 'POST':
        form_info = ArticleCreateForm(request.POST)
        if form_info.is_valid():
            try:
                cursor = connection.cursor()
                cursor.execute('BEGIN;')
            except ProgrammingError:
                response_message = '操作失败！'
                return render(request, 'control/manage/article_create.html', locals())

            insert_query = '''
            UPDATE blog_content
            SET title = '%s',
            slug = '%s',
            summary = '%s',
            text = '%s',
            edit_time = NOW()
            WHERE id = %s
            AND type = 'article';
            ''' % (request.POST['title'], request.POST['slug'],
                   content_operation(request.POST['summary']), content_operation(request.POST['text']), article_info.id)
            try:
                cursor = connection.cursor()
                cursor.execute(insert_query)
            except IntegrityError:
                response_message = '标识符已被占用！'
                cursor = connection.cursor()
                cursor.execute('ROLLBACK;')
                return render(request, 'control/manage/article_create.html', locals())
            except ProgrammingError:
                response_message = '操作失败！'
                cursor = connection.cursor()
                cursor.execute('ROLLBACK;')
                return render(request, 'control/manage/article_create.html', locals())

            meta_list = Relationship.objects.filter(content_id=article_info)
            try:
                for meta in meta_list:
                    meta.delete()
            except (KeyError, Relationship.DoesNotExist):
                response_message = '操作失败！'
                cursor = connection.cursor()
                cursor.execute('ROLLBACK;')
                return render(request, 'control/manage/article_create.html', locals())

            category_id_list = request.POST.getlist('category')
            tag_id_list = request.POST.getlist('tag')
            meta_id_list = category_id_list + tag_id_list

            if meta_id_list:
                meta_id_set = ''
                flag = 0
                for meta_id in meta_id_list:
                    if flag > 0:
                        meta_id_set += ', '
                    meta_id_set += ('(NULL, ' + str(article_id) + ', ' + str(meta_id) + ')')
                    flag += 1
                meta_insert_query = '''
                INSERT INTO blog_relationship
                VALUES %s;
                ''' % meta_id_set
                try:
                    cursor = connection.cursor()
                    cursor.execute(meta_insert_query)
                except ProgrammingError:
                    response_message = '操作失败！'
                    cursor = connection.cursor()
                    cursor.execute('ROLLBACK;')
                    return render(request, 'control/manage/article_create.html', locals())

            try:
                cursor = connection.cursor()
                cursor.execute('COMMIT;')
                return HttpResponseRedirect(reverse('control:article_list', args=()))
            except ProgrammingError:
                response_message = '操作失败！'
                return render(request, 'control/manage/article_create.html', locals())

        else:
            response_message = '请检查输入格式！'
            return render(request, 'control/manage/article_create.html', locals())

    article_info_dict = {
        'title': article_info.title,
        'slug': article_info.slug,
        'text': article_info.text,
        'summary': article_info.summary,
        'category': [],
        'tag': [],
    }

    category_list_query = '''
        SELECT meta_id_id, id
        FROM blog_relationship
        WHERE content_id_id = %s
        AND meta_id_id in (
            SELECT id
            FROM blog_meta
            WHERE type = 'category'
        );
    ''' % article_info.id
    category_list = Relationship.objects.raw(category_list_query)
    for category in category_list:
        article_info_dict['category'].append(category.meta_id.id)

    tag_list_query = '''
        SELECT meta_id_id, id
        FROM blog_relationship
        WHERE content_id_id = %s
        AND meta_id_id in (
            SELECT id
            FROM blog_meta
            WHERE type = 'tag'
        );
    ''' % article_info.id
    tag_list = Relationship.objects.raw(tag_list_query)
    for tag in tag_list:
        article_info_dict['tag'].append(tag.meta_id.id)

    form_info = ArticleCreateForm(article_info_dict)
    return render(request, 'control/manage/article_create.html', locals())


def page_create(request):
    if request.session.get('is_login') is None:
        return HttpResponseRedirect(reverse('control:login', args=()))

    if User.objects.get(id=request.session['user_id']).group != 'administrator' and User.objects.get(id=request.session['user_id']).group != 'writer':
        return HttpResponseRedirect(reverse('control:forbidden', args=()))

    response_message = ''

    if request.method == 'POST':
        form_info = PageCreateForm(request.POST)
        if form_info.is_valid():
            insert_query = '''
            INSERT INTO blog_content
            VALUES (NULL, '%s', '%s', NOW(), NOW(), '%s', '%s', %s, 'page', %s);
            ''' % (request.POST['title'], request.POST['slug'], request.POST['summary'].replace('\\', '\\\\'),
                   request.POST['text'].replace('\\', '\\\\'), request.POST['priority_id'], request.session['user_id'])
            try:
                cursor = connection.cursor()
                cursor.execute(insert_query)
                return HttpResponseRedirect(reverse('control:page_list', args=()))
            except IntegrityError:
                response_message = '标识符已被占用！'
                cursor = connection.cursor()
                return render(request, 'control/manage/page_create.html', locals())
            except ProgrammingError:
                response_message = '操作失败！'
                cursor = connection.cursor()
                return render(request, 'control/manage/page_create.html', locals())

        else:
            response_message = '请检查输入格式！'
            return render(request, 'control/manage/page_create.html', locals())

    form_info = PageCreateForm()
    return render(request, 'control/manage/page_create.html', locals())


def page_edit(request, page_id):
    if request.session.get('is_login') is None:
        return HttpResponseRedirect(reverse('control:login', args=()))

    if User.objects.get(id=request.session['user_id']).group != 'administrator' and User.objects.get(id=request.session['user_id']).group != 'writer':
        return HttpResponseRedirect(reverse('control:forbidden', args=()))

    page_info = None

    try:
        page_info = Content.objects.get(id=page_id, type='page')
    except (KeyError, Content.DoesNotExist):
        return HttpResponseRedirect(reverse('control:forbidden', args=()))

    if User.objects.get(id=request.session['user_id']).group == 'writer' and page_info.author_id.id != request.session['user_id']:
        return HttpResponseRedirect(reverse('control:forbidden', args=()))

    response_message = ''

    if request.method == 'POST':
        form_info = PageCreateForm(request.POST)
        if form_info.is_valid():
            insert_query = '''
            UPDATE blog_content
            SET title = '%s',
            slug = '%s',
            summary = '%s',
            text = '%s',
            edit_time = NOW(),
            priority_id = %s
            WHERE id = %s
            AND type = 'page';
            ''' % (request.POST['title'], request.POST['slug'], request.POST['summary'].replace('\\', '\\\\'),
                   request.POST['text'].replace('\\', '\\\\'), request.POST['priority_id'], page_info.id)
            try:
                cursor = connection.cursor()
                cursor.execute(insert_query)
                return HttpResponseRedirect(reverse('control:page_list', args=()))
            except IntegrityError:
                response_message = '标识符已被占用！'
                cursor = connection.cursor()
                return render(request, 'control/manage/page_create.html', locals())
            except ProgrammingError:
                response_message = '操作失败！'
                cursor = connection.cursor()
                return render(request, 'control/manage/page_create.html', locals())

        else:
            response_message = '请检查输入格式！'
            return render(request, 'control/manage/page_create.html', locals())

    page_info_dict = {
        'title': page_info.title,
        'slug': page_info.slug,
        'text': page_info.text,
        'summary': page_info.summary,
        'priority_id': page_info.priority_id,
    }

    form_info = PageCreateForm(page_info_dict)
    return render(request, 'control/manage/page_create.html', locals())


def category_list(request, page_id=1):
    if request.session.get('is_login') is None:
        return HttpResponseRedirect(reverse('control:login', args=()))

    if User.objects.get(id=request.session['user_id']).group != 'administrator' and User.objects.get(id=request.session['user_id']).group != 'writer':
        return HttpResponseRedirect(reverse('control:forbidden', args=()))

    if request.method == 'POST':
        category_id_list = request.POST.getlist('article_cid[]')
        category_id_set = ''
        if category_id_list:
            flag = 0
            for category_id in category_id_list:
                if flag > 0:
                    category_id_set += ', '
                category_id_set += category_id
                flag += 1
            operation_query = '''
            SELECT * FROM blog_meta
            WHERE id in (%s);
            ''' % category_id_set

            try:
                category_list = Meta.objects.raw(operation_query)
                for category in category_list:
                    category.delete()
            except (KeyError, Content.DoesNotExist):
                response_message = '删除失败！'

    keyword = request.GET.get('keyword')

    if keyword is None:
        keyword = ''

    page_size = 10
    basic_info = get_basic_info(request)
    if keyword == '':
        basic_info['number_of_category'] = Meta.objects.filter(type='category').count()
    else:
        basic_info['number_of_category'] = Meta.objects.filter(type='category', name__contains=keyword).count()
    basic_info['number_of_category_page'] = ceil(basic_info['number_of_category'], page_size)

    left_range = 0 + page_size * (page_id - 1)

    meta_list_query = '''
    SELECT id, name, slug
    FROM blog_meta
    WHERE type = 'category'
    '''

    if keyword != '':
        meta_list_query += '''
        AND name LIKE '%%%%%s%%%%'
        ''' % keyword

    meta_list_query += '''
    ORDER BY priority_id
    LIMIT %s, %s;
    ''' % (left_range, page_size)

    cursor = connection.cursor()
    cursor.execute(meta_list_query)
    meta_list = cursor.fetchall()

    form_info = MetaFilterForm({'keyword': keyword,})

    return render(request, 'control/manage/meta_list.html', locals())


def category_create(request):
    if request.session.get('is_login') is None:
        return HttpResponseRedirect(reverse('control:login', args=()))

    if User.objects.get(id=request.session['user_id']).group != 'administrator' and User.objects.get(id=request.session['user_id']).group != 'writer':
        return HttpResponseRedirect(reverse('control:forbidden', args=()))

    response_message = ''

    if request.method == 'POST':
        form_info = MetaCreateForm(request.POST)
        if form_info.is_valid():
            insert_query = '''
            INSERT INTO blog_meta
            VALUES (NULL, '%s', '%s', 'category', '%s', %s);
            ''' % (request.POST['name'], request.POST['slug'],
                   request.POST['description'], request.POST['priority_id'])
            try:
                cursor = connection.cursor()
                cursor.execute(insert_query)
                return HttpResponseRedirect(reverse('control:category_list', args=()))
            except IntegrityError:
                response_message = '标识符已被占用！'
                cursor = connection.cursor()
                return render(request, 'control/manage/meta_create.html', locals())
            except ProgrammingError:
                response_message = '操作失败！'
                cursor = connection.cursor()
                return render(request, 'control/manage/meta_create.html', locals())

        else:
            response_message = '请检查输入格式！'
            return render(request, 'control/manage/meta_create.html', locals())

    form_info = MetaCreateForm()
    return render(request, 'control/manage/meta_create.html', locals())


def category_edit(request, category_id):
    if request.session.get('is_login') is None:
        return HttpResponseRedirect(reverse('control:login', args=()))

    if User.objects.get(id=request.session['user_id']).group != 'administrator' and User.objects.get(id=request.session['user_id']).group != 'writer':
        return HttpResponseRedirect(reverse('control:forbidden', args=()))

    category_info = None

    try:
        category_info = Meta.objects.get(id=category_id, type='category')
    except (KeyError, Content.DoesNotExist):
        return HttpResponseRedirect(reverse('control:forbidden', args=()))

    response_message = ''

    if request.method == 'POST':
        form_info = MetaCreateForm(request.POST)
        if form_info.is_valid():
            insert_query = '''
            UPDATE blog_meta
            SET name = '%s',
            slug = '%s',
            description = '%s',
            priority_id = %s
            WHERE id = %s
            AND type = 'category';
            ''' % (request.POST['name'], request.POST['slug'], request.POST['description'],
                   request.POST['priority_id'], category_info.id)
            try:
                cursor = connection.cursor()
                cursor.execute(insert_query)
                return HttpResponseRedirect(reverse('control:category_list', args=()))
            except IntegrityError:
                response_message = '标识符已被占用！'
                cursor = connection.cursor()
                return render(request, 'control/manage/meta_create.html', locals())
            except ProgrammingError:
                response_message = '操作失败！'
                cursor = connection.cursor()
                return render(request, 'control/manage/meta_create.html', locals())

        else:
            response_message = '请检查输入格式！'
            return render(request, 'control/manage/meta_create.html', locals())

    category_info_dict = {
        'name': category_info.name,
        'slug': category_info.slug,
        'description': category_info.description,
        'priority_id': category_info.priority_id,
    }

    form_info = MetaCreateForm(category_info_dict)
    return render(request, 'control/manage/meta_create.html', locals())


def tag_list(request, page_id=1):
    if request.session.get('is_login') is None:
        return HttpResponseRedirect(reverse('control:login', args=()))

    if User.objects.get(id=request.session['user_id']).group != 'administrator' and User.objects.get(id=request.session['user_id']).group != 'writer':
        return HttpResponseRedirect(reverse('control:forbidden', args=()))

    if request.method == 'POST':
        tag_id_list = request.POST.getlist('article_cid[]')
        tag_id_set = ''
        if tag_id_list:
            flag = 0
            for tag_id in tag_id_list:
                if flag > 0:
                    tag_id_set += ', '
                tag_id_set += tag_id
                flag += 1
            operation_query = '''
            SELECT * FROM blog_meta
            WHERE id in (%s);
            ''' % tag_id_set

            try:
                tag_list = Meta.objects.raw(operation_query)
                for tag in tag_list:
                    tag.delete()
            except (KeyError, Content.DoesNotExist):
                response_message = '删除失败！'

    keyword = request.GET.get('keyword')

    if keyword is None:
        keyword = ''

    page_size = 10
    basic_info = get_basic_info(request)
    if keyword == '':
        basic_info['number_of_tag'] = Meta.objects.filter(type='tag').count()
    else:
        basic_info['number_of_tag'] = Meta.objects.filter(type='tag', name__contains=keyword).count()
    basic_info['number_of_tag_page'] = ceil(basic_info['number_of_tag'], page_size)

    left_range = 0 + page_size * (page_id - 1)

    meta_list_query = '''
    SELECT id, name, slug
    FROM blog_meta
    WHERE type = 'tag'
    '''

    if keyword != '':
        meta_list_query += '''
        AND name LIKE '%%%%%s%%%%'
        ''' % keyword

    meta_list_query += '''
    ORDER BY priority_id
    LIMIT %s, %s;
    ''' % (left_range, page_size)

    cursor = connection.cursor()
    cursor.execute(meta_list_query)
    meta_list = cursor.fetchall()

    form_info = MetaFilterForm({'keyword': keyword,})

    return render(request, 'control/manage/meta_list.html', locals())


def tag_create(request):
    if request.session.get('is_login') is None:
        return HttpResponseRedirect(reverse('control:login', args=()))

    if User.objects.get(id=request.session['user_id']).group != 'administrator' and User.objects.get(id=request.session['user_id']).group != 'writer':
        return HttpResponseRedirect(reverse('control:forbidden', args=()))

    response_message = ''

    if request.method == 'POST':
        form_info = MetaCreateForm(request.POST)
        if form_info.is_valid():
            insert_query = '''
            INSERT INTO blog_meta
            VALUES (NULL, '%s', '%s', 'tag', '%s', %s);
            ''' % (request.POST['name'], request.POST['slug'],
                   request.POST['description'], request.POST['priority_id'])
            try:
                cursor = connection.cursor()
                cursor.execute(insert_query)
                return HttpResponseRedirect(reverse('control:tag_list', args=()))
            except IntegrityError:
                response_message = '标识符已被占用！'
                cursor = connection.cursor()
                return render(request, 'control/manage/meta_create.html', locals())
            except ProgrammingError:
                response_message = '操作失败！'
                cursor = connection.cursor()
                return render(request, 'control/manage/meta_create.html', locals())

        else:
            response_message = '请检查输入格式！'
            return render(request, 'control/manage/meta_create.html', locals())

    form_info = MetaCreateForm()
    return render(request, 'control/manage/meta_create.html', locals())


def tag_edit(request, tag_id):
    if request.session.get('is_login') is None:
        return HttpResponseRedirect(reverse('control:login', args=()))

    if User.objects.get(id=request.session['user_id']).group != 'administrator' and User.objects.get(id=request.session['user_id']).group != 'writer':
        return HttpResponseRedirect(reverse('control:forbidden', args=()))

    tag_info = None

    try:
        tag_info = Meta.objects.get(id=tag_id, type='tag')
    except (KeyError, Content.DoesNotExist):
        return HttpResponseRedirect(reverse('control:forbidden', args=()))

    response_message = ''

    if request.method == 'POST':
        form_info = MetaCreateForm(request.POST)
        if form_info.is_valid():
            insert_query = '''
            UPDATE blog_meta
            SET name = '%s',
            slug = '%s',
            description = '%s',
            priority_id = %s
            WHERE id = %s
            AND type = 'tag';
            ''' % (request.POST['name'], request.POST['slug'], request.POST['description'],
                   request.POST['priority_id'], tag_info.id)
            try:
                cursor = connection.cursor()
                cursor.execute(insert_query)
                return HttpResponseRedirect(reverse('control:tag_list', args=()))
            except IntegrityError:
                response_message = '标识符已被占用！'
                cursor = connection.cursor()
                return render(request, 'control/manage/meta_create.html', locals())
            except ProgrammingError:
                response_message = '操作失败！'
                cursor = connection.cursor()
                return render(request, 'control/manage/meta_create.html', locals())

        else:
            response_message = '请检查输入格式！'
            return render(request, 'control/manage/meta_create.html', locals())

    tag_info_dict = {
        'name': tag_info.name,
        'slug': tag_info.slug,
        'description': tag_info.description,
        'priority_id': tag_info.priority_id,
    }

    form_info = MetaCreateForm(tag_info_dict)
    return render(request, 'control/manage/meta_create.html', locals())


def user_list(request, page_id=1):
    if request.session.get('is_login') is None:
        return HttpResponseRedirect(reverse('control:login', args=()))

    if User.objects.get(id=request.session['user_id']).group != 'administrator':
        return HttpResponseRedirect(reverse('control:forbidden', args=()))

    if request.method == 'POST':
        user_id_list = request.POST.getlist('article_cid[]')
        user_id_set = ''
        if user_id_list:
            flag = 0
            for user_id in user_id_list:
                if int(user_id) == int(request.session['user_id']):
                    continue
                if flag > 0:
                    user_id_set += ', '
                user_id_set += user_id
                flag += 1
            if flag > 0:
                operation_query = '''
                SELECT * FROM blog_user
                WHERE id in (%s);
                ''' % user_id_set
                try:
                    user_list = User.objects.raw(operation_query)
                    for user in user_list:
                        user.delete()
                except (KeyError, Content.DoesNotExist):
                    response_message = '删除失败！'

    keyword = request.GET.get('keyword')

    if keyword is None:
        keyword = ''

    page_size = 10
    basic_info = get_basic_info(request)
    if keyword == '':
        basic_info['number_of_user'] = User.objects.all().count()
    else:
        basic_info['number_of_user'] = User.objects.filter(username__contains=keyword).count()
    basic_info['number_of_user_page'] = ceil(basic_info['number_of_user'], page_size)

    left_range = 0 + page_size * (page_id - 1)

    user_list_query = '''
    SELECT id, username, nickname, last_login_time
    FROM blog_user
    '''

    if keyword != '':
        user_list_query += '''
        WHERE username LIKE '%%%%%s%%%%'
        ''' % keyword

    user_list_query += '''
    ORDER BY create_time DESC
    LIMIT %s, %s;
    ''' % (left_range, page_size)

    cursor = connection.cursor()
    cursor.execute(user_list_query)
    user_list = cursor.fetchall()

    form_info = UserFilterForm({'keyword': keyword,})
    return render(request, 'control/manage/user_list.html', locals())


def user_create(request):
    if request.session.get('is_login') is None:
        return HttpResponseRedirect(reverse('control:login', args=()))

    if User.objects.get(id=request.session['user_id']).group != 'administrator':
        return HttpResponseRedirect(reverse('control:forbidden', args=()))

    response_message = ''

    if request.method == 'POST':
        form_info = UserCreateForm(request.POST)
        if form_info.is_valid():
            password = password_encrypt(request.POST['password'])
            group_slug = ''
            if int(request.POST['group']) == 0:
                group_slug = 'administrator'
            elif int(request.POST['group']) == 1:
                group_slug = 'writer'
            else:
                group_slug = 'user'
            insert_query = '''
            INSERT INTO blog_user
            VALUES (NULL, '%s', '%s', '%s', '%s', '%s', NOW(), NOW(), '%s');
            ''' % (request.POST['username'], password, request.POST['mail'],
                   request.POST['url'], request.POST['nickname'], group_slug)
            try:
                cursor = connection.cursor()
                cursor.execute(insert_query)
                return HttpResponseRedirect(reverse('control:user_list', args=()))
            except IntegrityError:
                response_message = '用户名/邮箱/昵称已被占用！'
                cursor = connection.cursor()
                return render(request, 'control/manage/user_create.html', locals())
            except ProgrammingError:
                response_message = '操作失败！'
                cursor = connection.cursor()
                return render(request, 'control/manage/user_create.html', locals())

        else:
            response_message = '请检查输入格式！'
            return render(request, 'control/manage/user_create.html', locals())

    form_info = UserCreateForm()
    return render(request, 'control/manage/user_create.html', locals())


def user_edit(request, user_id):
    if request.session.get('is_login') is None:
        return HttpResponseRedirect(reverse('control:login', args=()))

    if User.objects.get(id=request.session['user_id']).group != 'administrator':
        return HttpResponseRedirect(reverse('control:forbidden', args=()))

    user_info = None

    try:
        user_info = User.objects.get(id=user_id)
    except (KeyError, Content.DoesNotExist):
        return HttpResponseRedirect(reverse('control:forbidden', args=()))

    response_message = ''

    if request.method == 'POST':
        form_info = UserEditForm(request.POST)
        if form_info.is_valid():
            password = password_encrypt(request.POST['password'])
            group_slug = ''
            if int(request.POST['group']) == 0:
                group_slug = 'administrator'
            elif int(request.POST['group']) == 1:
                group_slug = 'writer'
            else:
                group_slug = 'user'

            insert_query = '''
            UPDATE blog_user
            SET username = '%s',
            ''' % request.POST['username']

            if request.POST['password'] != '':
                insert_query += '''
                password = '%s',
                ''' % password

            insert_query += '''
            mail = '%s',
            url = '%s',
            nickname = '%s',
            `group` = '%s'
            WHERE id = %s;
            ''' % (request.POST['mail'], request.POST['url'],
                   request.POST['nickname'], group_slug, user_info.id)
            print(insert_query)

            try:
                cursor = connection.cursor()
                cursor.execute(insert_query)
                return HttpResponseRedirect(reverse('control:user_list', args=()))
            except IntegrityError:
                response_message = '用户名/邮箱/昵称已被占用！'
                cursor = connection.cursor()
                return render(request, 'control/manage/user_create.html', locals())
            except ProgrammingError:
                response_message = '操作失败！'
                cursor = connection.cursor()
                return render(request, 'control/manage/user_create.html', locals())

        else:
            response_message = '请检查输入格式！'
            return render(request, 'control/manage/user_create.html', locals())

    group_id = None;
    if user_info.group == 'administrator':
        group_id = 0
    elif user_info.group == 'writer':
        group_id = 1
    else:
        group_id = 2

    user_info_dict = {
        'username': user_info.username,
        'mail': user_info.mail,
        'url': user_info.url,
        'nickname': user_info.nickname,
        'group': group_id,
    }

    form_info = UserEditForm(user_info_dict)
    return render(request, 'control/manage/user_create.html', locals())


def comment_list(request, page_id=1):
    if request.session.get('is_login') is None:
        return HttpResponseRedirect(reverse('control:login', args=()))

    if User.objects.get(id=request.session['user_id']).group != 'administrator' and User.objects.get(id=request.session['user_id']).group != 'writer':
        return HttpResponseRedirect(reverse('control:forbidden', args=()))

    if request.method == 'POST':
        print(request.POST)
        if request.POST['operation'] == 'comment_submit':
            if request.META.get('HTTP_X_FORWARDED_FOR') is not None:
                ip = request.META['HTTP_X_FORWARDED_FOR']
            else:
                ip = request.META['REMOTE_ADDR']

            try:
                comment_info = Comment.objects.get(id=int(request.POST['id']))
            except (KeyError, Content.DoesNotExist):
                return HttpResponseRedirect(reverse('control:forbidden', args=()))

            comment_commit_query = '''
            INSERT INTO blog_comment
            VALUES (NULL, '%s', '%s', '%s', 'approved', '%s', %s, %s, %s);
            ''' % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                   ip, request.POST['text'], request.session['user_id'], comment_info.content_id.id, request.POST['id'])

            try:
                cursor = connection.cursor()
                cursor.execute(comment_commit_query)
            except ProgrammingError:
                response_message = '操作失败！'
                cursor = connection.cursor()

        else:
            comment_id_list = request.POST.getlist('article_cid[]')
            comment_id_set = ''
            flag = 0
            for comment_id in comment_id_list:
                if flag > 0:
                    comment_id_set += ', '
                comment_id_set += comment_id
                flag += 1

            operation_query = '''
                    SELECT * FROM blog_comment
                    WHERE id in (%s)
                    ''' % comment_id_set

            if User.objects.get(id=request.session['user_id']).group == 'writer':
                operation_query += '''
                        AND content_id_id in (
                            SELECT id
                            FROM blog_content
                            WHERE author_id_id = %s
                        )
                        ''' % request.session['user_id']

            if flag > 0 and request.POST['operation'] == 'delete':
                try:
                    comment_list = Comment.objects.raw(operation_query)
                    for comment in comment_list:
                        comment.delete()
                except (KeyError, Content.DoesNotExist):
                    response_message = '删除失败！'

            elif flag > 0:
                try:
                    comment_list = Comment.objects.raw(operation_query)
                    for comment in comment_list:
                        if request.POST['operation'] == 'pass':
                            comment.status = 'approved'
                        else:
                            comment.status = 'rejected'
                        comment.save()
                except (KeyError, Content.DoesNotExist):
                    response_message = '操作失败！'

    keyword = request.GET.get('keyword')

    if keyword is None:
        keyword = ''

    number_of_comment_query = '''
    SELECT COUNT(id) FROM blog_comment
    '''

    if User.objects.get(id=request.session['user_id']).group == 'writer':
        number_of_comment_query += '''
        WHERE content_id_id in (
            SELECT id
            FROM blog_content
            WHERE author_id_id = %s
        )
        ''' % request.session['user_id']

    if keyword != '':
        number_of_comment_query += '''
        WHERE text LIKE '%%%%%s%%%%'
        ''' % keyword

    page_size = 10
    basic_info = get_basic_info(request)
    cursor = connection.cursor()
    cursor.execute(number_of_comment_query)
    basic_info['number_of_comment'] = cursor.fetchone()[0]
    basic_info['number_of_comment_page'] = ceil(basic_info['number_of_comment'], page_size)

    left_range = 0 + page_size * (page_id - 1)

    comment_list_query = '''
    SELECT id, author_id_id, content_id_id, text, status, status, create_time
    FROM blog_comment
    '''

    if User.objects.get(id=request.session['user_id']).group == 'writer':
        comment_list_query += '''
        WHERE content_id_id in (
            SELECT id
            FROM blog_content
            WHERE author_id_id = %s
        )
        ''' % request.session['user_id']

    if keyword != '':
        comment_list_query += '''
        WHERE text LIKE '%%%%%s%%%%'
        ''' % keyword

    comment_list_query += '''
    ORDER BY create_time DESC
    LIMIT %s, %s;
    ''' % (left_range, page_size)

    cursor = connection.cursor()
    cursor.execute(comment_list_query)
    comment_list = list(cursor.fetchall())

    for i in range(0, len(comment_list)):
        comment_list[i] = list(comment_list[i])
        comment_list[i][1] = User.objects.get(id=comment_list[i][1]).nickname
        content_info = Content.objects.get(id=comment_list[i][2])
        comment_list[i][2] = content_info.title
        comment_list[i][5] = content_info.slug

    form_info = CommentFilterForm({'keyword': keyword,})
    comment_commit_form_info = CommentCreateForm()

    return render(request, 'control/manage/comment_list.html', locals())


def link_list(request, page_id=1):
    if request.session.get('is_login') is None:
        return HttpResponseRedirect(reverse('control:login', args=()))

    if User.objects.get(id=request.session['user_id']).group != 'administrator':
        return HttpResponseRedirect(reverse('control:forbidden', args=()))

    if request.method == 'POST':
        link_id_list = request.POST.getlist('article_cid[]')
        link_id_set = ''
        if link_id_list:
            flag = 0
            for link_id in link_id_list:
                if flag > 0:
                    link_id_set += ', '
                link_id_set += link_id
                flag += 1
            operation_query = '''
            SELECT * FROM blog_link
            WHERE id in (%s);
            ''' % link_id_set

            try:
                link_list = Link.objects.raw(operation_query)
                for link in link_list:
                    link.delete()
            except (KeyError, Content.DoesNotExist):
                response_message = '删除失败！'

    keyword = request.GET.get('keyword')

    if keyword is None:
        keyword = ''

    page_size = 10
    basic_info = get_basic_info(request)
    if keyword == '':
        basic_info['number_of_link'] = Link.objects.all().count()
    else:
        basic_info['number_of_link'] = Link.objects.filter(name__contains=keyword).count()
    basic_info['number_of_link_page'] = ceil(basic_info['number_of_link'], page_size)

    left_range = 0 + page_size * (page_id - 1)

    link_list_query = '''
    SELECT id, name, url
    FROM blog_link
    '''

    if keyword != '':
        link_list_query += '''
        WHERE name LIKE '%%%s%%'
        ''' % keyword

    link_list_query += '''
    LIMIT %s, %s;
    ''' % (left_range, page_size)

    cursor = connection.cursor()
    cursor.execute(link_list_query)
    link_list = cursor.fetchall()

    form_info = LinkFilterForm({'keyword': keyword,})

    return render(request, 'control/manage/link_list.html', locals())


def link_create(request):
    if request.session.get('is_login') is None:
        return HttpResponseRedirect(reverse('control:login', args=()))

    if User.objects.get(id=request.session['user_id']).group != 'administrator':
        return HttpResponseRedirect(reverse('control:forbidden', args=()))

    response_message = ''

    if request.method == 'POST':
        form_info = LinkCreateForm(request.POST)
        if form_info.is_valid():
            insert_query = '''
            INSERT INTO blog_link
            VALUES (NULL, '%s', '%s');
            ''' % (request.POST['name'], request.POST['url'])
            try:
                cursor = connection.cursor()
                cursor.execute(insert_query)
                return HttpResponseRedirect(reverse('control:link_list', args=()))
            except ProgrammingError:
                response_message = '操作失败！'
                cursor = connection.cursor()
                return render(request, 'control/manage/link_create.html', locals())

        else:
            response_message = '请检查输入格式！'
            return render(request, 'control/manage/link_create.html', locals())

    form_info = LinkCreateForm()
    return render(request, 'control/manage/link_create.html', locals())


def link_edit(request, link_id):
    if request.session.get('is_login') is None:
        return HttpResponseRedirect(reverse('control:login', args=()))

    if User.objects.get(id=request.session['user_id']).group != 'administrator':
        return HttpResponseRedirect(reverse('control:forbidden', args=()))

    link_info = None

    try:
        link_info = Link.objects.get(id=link_id)
    except (KeyError, Content.DoesNotExist):
        return HttpResponseRedirect(reverse('control:forbidden', args=()))

    response_message = ''

    if request.method == 'POST':
        form_info = LinkCreateForm(request.POST)
        if form_info.is_valid():
            insert_query = '''
            UPDATE blog_link
            SET name = '%s',
            url = '%s'
            WHERE id = %s;
            ''' % (request.POST['name'], request.POST['url'], link_id)
            try:
                cursor = connection.cursor()
                cursor.execute(insert_query)
                return HttpResponseRedirect(reverse('control:link_list', args=()))
            except ProgrammingError:
                response_message = '操作失败！'
                cursor = connection.cursor()
                return render(request, 'control/manage/link_create.html', locals())

        else:
            response_message = '请检查输入格式！'
            return render(request, 'control/manage/link_create.html', locals())

    link_info_dict = {
        'name': link_info.name,
        'url': link_info.url,
    }

    form_info = LinkCreateForm(link_info_dict)
    return render(request, 'control/manage/link_create.html', locals())


def setting(request):
    if request.session.get('is_login') is None:
        return HttpResponseRedirect(reverse('control:login', args=()))

    if User.objects.get(id=request.session['user_id']).group != 'administrator':
        return HttpResponseRedirect(reverse('control:forbidden', args=()))

    response_message = ''
    setting_data_list = Setting.objects.all()

    if request.method == 'POST':
        form_info = SettingForm(request.POST)
        if form_info.is_valid():
            try:
                cursor = connection.cursor()
                cursor.execute('BEGIN;')
            except ProgrammingError:
                response_message = '操作失败！'
                return render(request, 'control/general/setting.html', locals())

            is_success = True
            for setting_data in setting_data_list:
                operation_query = '''
                            UPDATE blog_setting
                            SET value = '%s'
                            WHERE name = '%s';
                            ''' % (request.POST[setting_data.name], setting_data.name)

                try:
                    cursor = connection.cursor()
                    cursor.execute(operation_query)
                    response_message = '更新成功！'
                except ProgrammingError:
                    cursor = connection.cursor()
                    cursor.execute('ROLLBACK;')
                    response_message = '更新失败！'
                    is_success = False
                    break

            if is_success:
                try:
                    cursor = connection.cursor()
                    cursor.execute('COMMIT;')
                except ProgrammingError:
                    response_message = '操作失败！'
                    return render(request, 'control/general/setting.html', locals())
        else:
            response_message = '请检查输入格式！'

    form_info = SettingForm()
    form_info['blog_name'].initial = Setting.objects.get(name='blog_name').value
    form_info['page_size'].initial = Setting.objects.get(name='page_size').value
    form_info['meta_page_size'].initial = Setting.objects.get(name='meta_page_size').value
    form_info['github'].initial = Setting.objects.get(name='github').value
    form_info['weibo'].initial = Setting.objects.get(name='weibo').value
    return render(request, 'control/general/setting.html', locals())
