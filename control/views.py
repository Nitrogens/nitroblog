from django.shortcuts import render, render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.urls import reverse
from django.db.models import F
from django.db import connection
import hashlib, base64


from blog.models import *
from .forms import LoginForm


def password_encrypt(password, salt='segmentation_fault'):
    hash_class = hashlib.sha256()
    password += salt
    hash_class.update(password.encode())
    return hash_class.hexdigest()


def login(request, source_url=None):
    if source_url is not None:
        source_url = base64.b64decode(source_url)

    if request.session.get('is_login', None):
        if source_url is None:
            return HttpResponseRedirect(reverse('control:dashboard', args=()))
        else:
            return HttpResponseRedirect(source_url)

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
                    if source_url is None:
                        return HttpResponseRedirect(reverse('control:dashboard', args=()))
                    else:
                        return HttpResponseRedirect(source_url)
                else:
                    login_message = '用户名或密码错误！'
            except User.DoesNotExist:
                login_message = '用户名或密码错误！'
        else:
            login_message = '请检查输入格式！'

    form_info = LoginForm()
    return render(request, 'control/login.html', locals())


def logout(request, destination_url=None):
    if destination_url is not None:
        destination_url = base64.b64decode(destination_url)

    if not request.session.get('is_login', None):
        if destination_url is None:
            return HttpResponseRedirect(reverse('control:login', args=()))
        else:
            return HttpResponseRedirect(destination_url)

    request.session.flush()

    if destination_url is None:
        return HttpResponseRedirect(reverse('control:login', args=()))
    else:
        return HttpResponseRedirect(destination_url)


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
    WHERE type = "article"
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

    return render(request, 'control/dashboard.html', context)
