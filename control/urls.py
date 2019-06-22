from django.urls import path

from . import views


app_name = 'control'
urlpatterns = [
    path('login/', views.login, name='login'),
    path('login/<str:source_url>/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('logout/<str:destination_url>/', views.logout, name='logout'),
    path('forbidden/', views.forbidden, name='forbidden'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('personal-information/', views.personal_information, name='personal_information'),
    path('change-password/', views.change_password, name='change_password'),
    path('manage/article/', views.article_list, name='article_list'),
    path('manage/article/page/<int:page_id>/', views.article_list, name='article_list'),
    path('manage/single-page/', views.page_list, name='page_list'),
    path('manage/single-page/page/<int:page_id>/', views.page_list, name='page_list'),
    path('manage/category/', views.category_list, name='category_list'),
    path('manage/category/page/<int:page_id>/', views.category_list, name='category_list'),
    path('manage/tag/', views.tag_list, name='tag_list'),
    path('manage/tag/page/<int:page_id>/', views.tag_list, name='tag_list'),
    path('create/article/', views.article_create, name='article_create'),
    path('create/page/', views.page_create, name='page_create'),
    path('create/category/', views.category_create, name='category_create'),
    path('create/tag/', views.tag_create, name='tag_create'),
    path('edit/article/<int:article_id>/', views.article_edit, name='article_edit'),
    path('edit/page/<int:page_id>/', views.page_edit, name='page_edit'),
    path('edit/category/<int:category_id>/', views.category_edit, name='category_edit'),
    path('edit/tag/<int:tag_id>/', views.tag_edit, name='tag_edit'),
]