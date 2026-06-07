from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    Category,
    Comment,
    ContentReport,
    DirectMessage,
    DirectMessageAttachment,
    Follow,
    HiddenPost,
    Like,
    Notification,
    Post,
    PostAttachment,
    Profile,
    SavedPost,
    UserBlock,
)

admin.site.site_header = 'VibeLog — администрирование'
admin.site.site_title = 'Админка VibeLog'
admin.site.index_title = 'Панель управления'
admin.site.index_template = 'admin/vibel_index.html'

LIST_PER_PAGE = 30


def admin_index_stats(request):
    return {
        'posts': Post.objects.count(),
        'users': User.objects.count(),
        'reports': ContentReport.objects.count(),
        'messages': DirectMessage.objects.count(),
        'unread_notifications': Notification.objects.filter(is_read=False).count(),
        'drafts': Post.objects.filter(visibility=Post.VIS_DRAFT).count(),
    }


_original_admin_index = admin.site.index


def custom_admin_index(request, extra_context=None):
    extra_context = extra_context or {}
    extra_context['vl_admin_stats'] = admin_index_stats(request)
    return _original_admin_index(request, extra_context=extra_context)


admin.site.index = custom_admin_index


@admin.action(description='Отметить прочитанными')
def mark_notifications_read(modeladmin, request, queryset):
    queryset.update(is_read=True)


@admin.action(description='Отметить непрочитанными')
def mark_notifications_unread(modeladmin, request, queryset):
    queryset.update(is_read=False)


@admin.action(description='Сделать публичными')
def make_posts_public(modeladmin, request, queryset):
    queryset.update(visibility=Post.VIS_PUBLIC)


@admin.action(description='Скрыть (только для себя)')
def make_posts_private(modeladmin, request, queryset):
    queryset.update(visibility=Post.VIS_PRIVATE)


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    extra = 0
    fieldsets = (
        (
            None,
            {
                'fields': (
                    'display_name',
                    'bio',
                    'location',
                    'avatar',
                    'cover',
                    'is_private',
                ),
            },
        ),
        (
            'Уведомления',
            {
                'classes': ('collapse',),
                'fields': (
                    'notify_likes',
                    'notify_comments',
                    'notify_follows',
                    'notify_mentions',
                ),
            },
        ),
    )


class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'display_name', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'profile__display_name')
    ordering = ('-date_joined',)
    list_per_page = LIST_PER_PAGE

    @admin.display(description='Имя в ленте')
    def display_name(self, obj):
        return getattr(obj.profile, 'display_name', '') or '—'


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'display_name', 'is_private', 'location', 'updated_at')
    list_filter = ('is_private',)
    search_fields = ('user__username', 'display_name', 'bio', 'location')
    autocomplete_fields = ('user',)
    list_per_page = LIST_PER_PAGE
    fieldsets = (
        ('Профиль', {'fields': ('user', 'display_name', 'bio', 'location', 'avatar', 'cover', 'is_private')}),
        (
            'Уведомления',
            {
                'classes': ('collapse',),
                'fields': (
                    'notify_likes',
                    'notify_comments',
                    'notify_follows',
                    'notify_mentions',
                ),
            },
        ),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order', 'posts_count')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('order', 'name')
    search_fields = ('name', 'slug')
    list_per_page = LIST_PER_PAGE

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_posts=Count('posts'))

    @admin.display(description='Постов')
    def posts_count(self, obj):
        return obj._posts


class PostAttachmentInline(admin.TabularInline):
    model = PostAttachment
    extra = 0
    fields = ('image', 'sort_order')
    ordering = ('sort_order',)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'author',
        'category',
        'visibility',
        'media_type',
        'attachments_count',
        'likes_count',
        'created_at',
    )
    list_display_links = ('id', 'author')
    list_filter = ('category', 'visibility', 'created_at')
    search_fields = ('caption', 'author__username', 'author__profile__display_name')
    readonly_fields = ('likes_count', 'created_at', 'updated_at', 'preview_main')
    inlines = (PostAttachmentInline,)
    date_hierarchy = 'created_at'
    autocomplete_fields = ('author', 'category')
    ordering = ('-created_at',)
    list_per_page = LIST_PER_PAGE
    actions = (make_posts_public, make_posts_private)
    fieldsets = (
        ('Основное', {'fields': ('author', 'category', 'caption', 'visibility')}),
        ('Фото', {'fields': ('preview_main', 'image')}),
        (
            'Видео (клип)',
            {
                'classes': ('collapse',),
                'fields': (
                    'video',
                    'video_clip_limit_s',
                    'video_clip_start_s',
                    'video_clip_end_s',
                ),
            },
        ),
        (
            'Служебное',
            {
                'classes': ('collapse',),
                'fields': ('likes_count', 'created_at', 'updated_at'),
            },
        ),
    )

    @admin.display(description='Превью')
    def preview_main(self, obj):
        if obj.pk and obj.image:
            return format_html(
                '<img src="{}" alt="" style="max-height:120px;border-radius:8px;">',
                obj.image.url,
            )
        if obj.pk and obj.video:
            return format_html(
                '<video src="{}" controls style="max-height:120px;border-radius:8px;"></video>',
                obj.video.url,
            )
        return '—'

    @admin.display(description='Медиа')
    def media_type(self, obj):
        if obj.video:
            return 'Видео'
        if obj.image:
            return 'Фото'
        if obj.attachments.exists():
            return 'Только вложения'
        return '—'

    @admin.display(description='Доп. фото')
    def attachments_count(self, obj):
        return obj.attachments.count()


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('follower', 'following', 'created_at')
    search_fields = ('follower__username', 'following__username')
    autocomplete_fields = ('follower', 'following')
    date_hierarchy = 'created_at'
    list_per_page = LIST_PER_PAGE


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'created_at')
    search_fields = ('user__username', 'post__id')
    autocomplete_fields = ('user', 'post')
    date_hierarchy = 'created_at'
    list_per_page = LIST_PER_PAGE


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'post', 'text_preview', 'has_image', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('text', 'author__username', 'post__id')
    autocomplete_fields = ('author', 'post')
    readonly_fields = ('created_at', 'preview_image')
    date_hierarchy = 'created_at'
    list_per_page = LIST_PER_PAGE
    fieldsets = (
        (None, {'fields': ('post', 'author', 'text', 'preview_image', 'image')}),
        ('Дата', {'fields': ('created_at',)}),
    )

    @admin.display(description='Текст')
    def text_preview(self, obj):
        t = (obj.text or '').strip()
        return t[:60] + ('…' if len(t) > 60 else '') if t else '—'

    @admin.display(boolean=True, description='Фото')
    def has_image(self, obj):
        return bool(obj.image)

    @admin.display(description='Превью')
    def preview_image(self, obj):
        if obj.pk and obj.image:
            return format_html(
                '<img src="{}" alt="" style="max-height:100px;border-radius:8px;">',
                obj.image.url,
            )
        return '—'


@admin.register(SavedPost)
class SavedPostAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'created_at')
    autocomplete_fields = ('user', 'post')
    date_hierarchy = 'created_at'
    list_per_page = LIST_PER_PAGE


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        'recipient',
        'actor',
        'event_type',
        'post',
        'is_read',
        'created_at',
    )
    list_filter = ('event_type', 'is_read', 'created_at')
    search_fields = ('recipient__username', 'actor__username', 'text')
    autocomplete_fields = ('recipient', 'actor', 'post')
    list_editable = ('is_read',)
    actions = (mark_notifications_read, mark_notifications_unread)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    list_per_page = LIST_PER_PAGE


@admin.register(HiddenPost)
class HiddenPostAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'created_at')
    autocomplete_fields = ('user', 'post')
    date_hierarchy = 'created_at'
    list_per_page = LIST_PER_PAGE


@admin.register(UserBlock)
class UserBlockAdmin(admin.ModelAdmin):
    list_display = ('blocker', 'blocked', 'created_at')
    search_fields = ('blocker__username', 'blocked__username')
    autocomplete_fields = ('blocker', 'blocked')
    date_hierarchy = 'created_at'
    list_per_page = LIST_PER_PAGE


@admin.register(ContentReport)
class ContentReportAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'reporter',
        'target_type',
        'target_id',
        'target_link',
        'reason_preview',
        'created_at',
    )
    list_filter = ('target_type', 'created_at')
    search_fields = ('reporter__username', 'reason', 'target_id')
    readonly_fields = ('created_at', 'reporter', 'target_type', 'target_id')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    list_per_page = LIST_PER_PAGE
    fieldsets = (
        ('Жалоба', {'fields': ('reporter', 'target_type', 'target_id', 'reason')}),
        ('Дата', {'fields': ('created_at',)}),
    )

    @admin.display(description='Причина')
    def reason_preview(self, obj):
        r = (obj.reason or '').strip()
        return r[:50] + ('…' if len(r) > 50 else '') if r else '—'

    @admin.display(description='Объект')
    def target_link(self, obj):
        url = None
        label = f'ID {obj.target_id}'
        if obj.target_type == ContentReport.TARGET_POST:
            url = reverse('admin:vibel_post_change', args=[obj.target_id])
            label = 'Открыть пост'
        elif obj.target_type == ContentReport.TARGET_COMMENT:
            url = reverse('admin:vibel_comment_change', args=[obj.target_id])
            label = 'Открыть комментарий'
        elif obj.target_type == ContentReport.TARGET_DM:
            url = reverse('admin:vibel_directmessage_change', args=[obj.target_id])
            label = 'Открыть сообщение'
        if url:
            return format_html('<a href="{}">{}</a>', url, label)
        return label


class DirectMessageAttachmentInline(admin.TabularInline):
    model = DirectMessageAttachment
    extra = 0
    fields = ('image', 'sort_order')


@admin.register(DirectMessage)
class DirectMessageAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'sender',
        'recipient',
        'body_preview',
        'is_read',
        'created_at',
    )
    list_filter = ('created_at',)
    search_fields = ('body', 'sender__username', 'recipient__username')
    autocomplete_fields = ('sender', 'recipient', 'reply_to')
    readonly_fields = ('created_at', 'read_at', 'edited_at')
    inlines = (DirectMessageAttachmentInline,)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    list_per_page = LIST_PER_PAGE
    fieldsets = (
        ('Сообщение', {'fields': ('sender', 'recipient', 'body', 'image', 'reply_to')}),
        ('Статус', {'fields': ('read_at', 'edited_at', 'created_at')}),
        (
            'Скрытие',
            {
                'classes': ('collapse',),
                'fields': ('hidden_for_sender_at', 'hidden_for_recipient_at'),
            },
        ),
    )

    @admin.display(description='Текст')
    def body_preview(self, obj):
        t = (obj.body or '').strip()
        return t[:50] + ('…' if len(t) > 50 else '') if t else '—'

    @admin.display(boolean=True, description='Прочитано')
    def is_read(self, obj):
        return obj.read_at is not None
