from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from . import views
from .forms import StyledAuthenticationForm

app_name = 'vibel'

urlpatterns = [
    path('', views.feed, name='feed'),
    path('settings/', views.settings_page, name='settings'),
    path('post/<int:post_id>/edit/', views.post_edit, name='post_edit'),
    path('post/<int:post_id>/delete/', views.post_delete, name='post_delete'),
    path('post/<int:post_id>/hide/', views.hide_post_toggle, name='hide_post_toggle'),
    path('u/<str:username>/block/', views.block_toggle, name='block_toggle'),
    path('report/', views.report_content, name='report_content'),
    path(
        'notifications/read-all/',
        views.notification_mark_all_read,
        name='notification_mark_all_read',
    ),
    path(
        'notifications/<int:notification_id>/read/',
        views.notification_mark_read,
        name='notification_mark_read',
    ),
    path(
        'messages/<str:username>/m/<int:message_id>/edit/',
        views.dm_message_edit,
        name='dm_message_edit',
    ),
    path('help/', views.help_page, name='help'),
    path('saved/', views.saved_posts, name='saved_posts'),
    path('notifications/', views.notifications_list, name='notifications'),
    path('messages/', views.messages_inbox, name='messages_inbox'),
    path(
        'messages/<str:username>/m/<int:message_id>/delete/',
        views.dm_message_delete,
        name='dm_message_delete',
    ),
    path('messages/<str:username>/', views.messages_thread, name='messages_thread'),
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('search/users/', views.user_search, name='user_search'),
    path('search/users/api/', views.user_search_api, name='user_search_api'),
    path('post/new/', views.post_create, name='post_create'),
    path('u/<str:username>/', views.profile_view, name='profile'),
    path('u/<str:username>/edit/', views.profile_edit, name='profile_edit'),
    path('follow/<str:username>/', views.follow_toggle, name='follow'),
    path('like/<int:post_id>/', views.like_toggle, name='like'),
    path('save/<int:post_id>/', views.save_toggle, name='save'),
    path('comment/<int:post_id>/', views.comment_create, name='comment_create'),
    path(
        'post/<int:post_id>/comment/<int:comment_id>/delete/',
        views.comment_delete,
        name='comment_delete',
    ),
    path('accounts/register/', views.register, name='register'),
    path(
        'accounts/login/',
        LoginView.as_view(
            template_name='vibel/login.html',
            authentication_form=StyledAuthenticationForm,
        ),
        name='login',
    ),
    path(
        'accounts/logout/',
        LogoutView.as_view(),
        name='logout',
    ),
]
