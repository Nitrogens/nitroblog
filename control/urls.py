from django.urls import path

from . import views


app_name = 'control'
urlpatterns = [
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('forbidden/', views.forbidden, name='forbidden'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('personal-information/', views.personal_information, name='personal_information'),
    path('change-password/', views.change_password, name='change_password'),
    path('setting/', views.setting, name='setting'),
    path('manage/article/', views.article_list, name='article_list'),
    path('manage/article/page/<int:page_id>/', views.article_list, name='article_list'),
    path('manage/single-page/', views.page_list, name='page_list'),
    path('manage/single-page/page/<int:page_id>/', views.page_list, name='page_list'),
    path('manage/category/', views.category_list, name='category_list'),
    path('manage/category/page/<int:page_id>/', views.category_list, name='category_list'),
    path('manage/tag/', views.tag_list, name='tag_list'),
    path('manage/tag/page/<int:page_id>/', views.tag_list, name='tag_list'),
    path('manage/user/', views.user_list, name='user_list'),
    path('manage/user/page/<int:page_id>/', views.user_list, name='user_list'),
    path('manage/comment/', views.comment_list, name='comment_list'),
    path('manage/comment/page/<int:page_id>/', views.comment_list, name='comment_list'),
    path('manage/link/', views.link_list, name='link_list'),
    path('manage/link/page/<int:page_id>/', views.link_list, name='link_list'),
    path('create/article/', views.article_create, name='article_create'),
    path('create/page/', views.page_create, name='page_create'),
    path('create/category/', views.category_create, name='category_create'),
    path('create/tag/', views.tag_create, name='tag_create'),
    path('create/user/', views.user_create, name='user_create'),
    path('create/link/', views.link_create, name='link_create'),
    path('edit/article/<int:article_id>/', views.article_edit, name='article_edit'),
    path('edit/page/<int:page_id>/', views.page_edit, name='page_edit'),
    path('edit/category/<int:category_id>/', views.category_edit, name='category_edit'),
    path('edit/tag/<int:tag_id>/', views.tag_edit, name='tag_edit'),
    path('edit/user/<int:user_id>/', views.user_edit, name='user_edit'),
    path('edit/link/<int:link_id>/', views.link_edit, name='link_edit'),
]