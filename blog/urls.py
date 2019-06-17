from django.urls import path

from . import views

app_name = 'blog'
urlpatterns = [
    path('', views.index, name='index'),
    path('page/<int:page_id>/', views.index, name='index'),
    # path('article/<str:article_slug>/', views.article, name='article'),
    # path('category/', views.category, name='category'),
    # path('category/page/<int:page_id>/', views.category, name='category'),
    # path('category/<str:category_slug>/', views.category_detail, name='category_detail'),
    # path('tag/', views.tag, name='tag'),
    # path('tag/page/<int:page_id>/', views.tag, name='tag'),
    # path('tag/<str:tag_slug>/', views.tag_detail, name='tag_detail'),
    # path('archive/', views.archive, name='archive'),
    # path('archive/page/<int:page_id>/', views.archive, name='archive'),
    # path('archive/<int:year>-<int:month>/', views.archive, name='archive_detail'),
    # path('link/', views.link, name='link'),
    # path('<str:page_slug>.html', views.article, name='page'),
]