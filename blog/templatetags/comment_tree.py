from django import template

from ..models import *

from datetime import timedelta, timezone


register = template.Library()


def find_parent(tree, comment):
    for key, value in tree.items():
        if key == comment.parent_id:
            tree[key][comment] = {}
            return
        else:
            find_parent(tree[key], comment)


def create_comment_tree(content_id):
    comment_list = Comment.objects.filter(content_id=content_id).order_by('create_time')
    comment_tree = {}

    for comment in comment_list:
        if comment.parent_id is None:
            comment_tree[comment] = {}
        else:
            find_parent(comment_tree, comment)

    return comment_tree


def dfs(tree):
    html_code = ''

    for key, value in tree.items():
        user_info = key.author_id
        user_name = user_info.username

        html_code += '''<div class="page-article-comment card" style="margin-left: 20px; margin-right: 10px;">
                        <div class="card-header">
                            <span class="badge badge-primary"><i class="fas fa-user"></i> %s</span>
                            <span class="badge badge-warning"><i class="fas fa-calendar-day"></i> %s</span>
                        </div>
                        <div class="card-body">
                            <p class="card-text">%s</p>
                        </div>
                ''' % (user_name, key.create_time.astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%I:%S'), key.text)

        if value:
            html_code += dfs(tree[key])

        html_code += '</div>'

    return html_code


@register.simple_tag
def get_comments(content_id):
    comment_tree = create_comment_tree(content_id)
    html_code = ''

    for key, value in comment_tree.items():
        user_info = key.author_id
        user_name = user_info.username

        html_code += '''<div class="page-article-comment card">
                                <div class="card-header">
                                    <span class="badge badge-primary"><i class="fas fa-user"></i> %s</span>
                                    <span class="badge badge-warning"><i class="fas fa-calendar-day"></i> %s</span>
                                </div>
                                <div class="card-body">
                                    <p class="card-text">%s</p>
                                </div>
                        ''' % (user_name, key.create_time.astimezone(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%I:%S'), key.text)

        if value:
            html_code += dfs(comment_tree[key])

        html_code += '</div>'

    return html_code
