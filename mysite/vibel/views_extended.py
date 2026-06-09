"""Дополнительные представления и хелперы ленты (пакет фич)."""

from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import logout
from django.db import DatabaseError
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .errors import WRITE_ERROR_MSG, respond_write_error
from .forms import (
    MAX_IMAGE_UPLOAD_BYTES,
    AccountDeleteForm,
    NotificationPrefsForm,
    PasswordChangeForm,
    PostEditForm,
    PostForm,
    ReportForm,
)
from .friends import are_friends
from .models import (
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
from .services import create_notification, notify_mentions
from .utils import blocked_user_ids, optimize_uploaded_image

FEED_PAGE_SIZE = 24
DM_EDIT_WINDOW = timedelta(minutes=15)


def feed_queryset(request, tab, cat_slug=''):
    qs = Post.objects.select_related(
        'author', 'category', 'author__profile'
    ).prefetch_related('attachments')

    if request.user.is_authenticated:
        hidden_ids = HiddenPost.objects.filter(user=request.user).values_list(
            'post_id', flat=True
        )
        qs = qs.exclude(pk__in=hidden_ids)
        blocked = blocked_user_ids(request.user)
        if blocked:
            qs = qs.exclude(author_id__in=blocked)
        qs = qs.filter(
            Q(visibility=Post.VIS_PUBLIC) | Q(author=request.user)
        )
        private_ids = list(
            Profile.objects.filter(is_private=True)
            .exclude(user=request.user)
            .values_list('user_id', flat=True)
        )
        if private_ids:
            following_ids = set(
                Follow.objects.filter(follower=request.user).values_list(
                    'following_id', flat=True
                )
            )
            hide_private = [uid for uid in private_ids if uid not in following_ids]
            if hide_private:
                qs = qs.exclude(author_id__in=hide_private)
    else:
        qs = qs.filter(visibility=Post.VIS_PUBLIC)
        private_ids = Profile.objects.filter(is_private=True).values_list(
            'user_id', flat=True
        )
        qs = qs.exclude(author_id__in=private_ids)

    if cat_slug:
        qs = qs.filter(category__slug=cat_slug)

    if tab == 'following':
        if request.user.is_authenticated:
            following_ids = Follow.objects.filter(follower=request.user).values_list(
                'following_id', flat=True
            )
            qs = qs.filter(author_id__in=following_ids).order_by('-created_at')
        else:
            qs = qs.order_by('-likes_count', '-created_at')
    elif tab == 'popular':
        qs = qs.order_by('-likes_count', '-created_at')
    else:
        qs = qs.order_by('-created_at')

    return qs


def paginate_feed(qs, page):
    page = max(1, page)
    start = (page - 1) * FEED_PAGE_SIZE
    end = start + FEED_PAGE_SIZE
    items = list(qs[start:end])
    has_more = qs[end : end + 1].exists()
    return items, has_more, page


def dm_hidden_for_viewer(dm, user):
    if dm.sender_id == user.id:
        return dm.hidden_for_sender_at is not None
    return dm.hidden_for_recipient_at is not None


@login_required
def settings_page(request):
    password_form = PasswordChangeForm(user=request.user)
    prefs_form = NotificationPrefsForm(instance=request.user.profile)
    delete_form = AccountDeleteForm()

    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'password':
            password_form = PasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                try:
                    password_form.save()
                except (DatabaseError, OSError, PermissionError, IOError):
                    messages.error(request, WRITE_ERROR_MSG)
                else:
                    messages.success(request, 'Пароль изменён.')
                    return redirect('vibel:settings')
        elif action == 'prefs':
            prefs_form = NotificationPrefsForm(
                request.POST, instance=request.user.profile
            )
            if prefs_form.is_valid():
                try:
                    prefs_form.save()
                except (DatabaseError, OSError, PermissionError, IOError):
                    messages.error(request, WRITE_ERROR_MSG)
                else:
                    messages.success(request, 'Настройки уведомлений сохранены.')
                    return redirect('vibel:settings')
        elif action == 'delete':
            delete_form = AccountDeleteForm(request.POST)
            if delete_form.is_valid():
                if not request.user.has_usable_password():
                    messages.error(
                        request,
                        'Удаление по паролю недоступно. Обратитесь к администратору.',
                    )
                    return redirect('vibel:settings')
                if not request.user.check_password(
                    delete_form.cleaned_data['password']
                ):
                    messages.error(request, 'Неверный пароль.')
                    return redirect('vibel:settings')
                try:
                    user = request.user
                    logout(request)
                    user.delete()
                except (DatabaseError, OSError, PermissionError, IOError):
                    messages.error(request, WRITE_ERROR_MSG)
                    return redirect('vibel:settings')
                return redirect('vibel:feed')

    return render(
        request,
        'vibel/settings.html',
        {
            'password_form': password_form,
            'prefs_form': prefs_form,
            'delete_form': delete_form,
        },
    )


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id, author=request.user)
    if request.method == 'POST':
        form = PostEditForm(request.POST, instance=post)
        if form.is_valid():
            try:
                form.save()
                post.updated_at = timezone.now()
                post.save(update_fields=['updated_at'])
            except (DatabaseError, OSError, PermissionError, IOError):
                messages.error(request, WRITE_ERROR_MSG)
            else:
                messages.success(request, 'Пост обновлён.')
                return redirect('vibel:post_detail', post_id=post.id)
    else:
        form = PostEditForm(instance=post)
    return render(
        request,
        'vibel/post_edit.html',
        {'form': form, 'post': post},
    )


@login_required
@require_POST
def post_delete(request, post_id):
    post = get_object_or_404(Post, id=post_id, author=request.user)
    try:
        post.delete()
    except (DatabaseError, OSError, PermissionError, IOError):
        return respond_write_error(request)
    messages.success(request, 'Пост удалён.')
    next_url = (request.POST.get('next') or '').strip()
    post_detail_path = reverse('vibel:post_detail', kwargs={'post_id': post_id})
    if next_url and post_detail_path in next_url.split('?')[0]:
        return redirect('vibel:feed')
    if next_url:
        return redirect(next_url)
    return redirect('vibel:feed')


def save_post_with_form(form, user, file_storage=None):
    """Сохраняет пост: первое фото в Post.image + остальные в PostAttachment."""
    import os

    if os.environ.get('VERCEL'):
        from vercel_bootstrap import ensure_media_dirs

        ensure_media_dirs()

    file_storage = file_storage or form.files
    from .forms import files_getlist

    images = [
        f for f in files_getlist(file_storage, 'images') if f and getattr(f, 'name', '')
    ]
    # Backward compat
    if not images:
        images = [
            f
            for f in files_getlist(file_storage, 'extra_images')
            if f and getattr(f, 'name', '')
        ]

    post = form.save(commit=False)
    post.author = user
    has_video = bool(form.cleaned_data.get('video'))

    attachment_files = []
    if post.image and images:
        # if legacy field posted, keep it as main and put the rest to attachments
        attachment_files = images
    elif images:
        post.image = optimize_uploaded_image(images[0])
        attachment_files = images[1:]
    elif has_video:
        post.image = ''

    try:
        post.save()
        for i, f in enumerate(attachment_files):
            if f.size > MAX_IMAGE_UPLOAD_BYTES:
                continue
            PostAttachment.objects.create(
                post=post,
                image=optimize_uploaded_image(f),
                sort_order=i,
            )
    except (DatabaseError, OSError, PermissionError, IOError):
        if post.pk:
            try:
                post.delete()
            except Exception:
                pass
        raise
    return post


@login_required
@require_POST
def hide_post_toggle(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    try:
        row = HiddenPost.objects.filter(user=request.user, post=post).first()
        hidden = False
        if row:
            row.delete()
        else:
            HiddenPost.objects.create(user=request.user, post=post)
            hidden = True
    except (DatabaseError, OSError, PermissionError, IOError):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'ok': False, 'error': WRITE_ERROR_MSG}, status=500)
        return respond_write_error(request)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'ok': True, 'hidden': hidden})
    return redirect(request.POST.get('next') or 'vibel:feed')


@login_required
@require_POST
def block_toggle(request, username):
    target = get_object_or_404(User, username=username)
    if target == request.user:
        return redirect('vibel:profile', username=username)
    try:
        rel = UserBlock.objects.filter(blocker=request.user, blocked=target)
        blocked = False
        if rel.exists():
            rel.delete()
            messages.info(request, f'@{target.username} разблокирован.')
        else:
            UserBlock.objects.create(blocker=request.user, blocked=target)
            Follow.objects.filter(
                Q(follower=request.user, following=target)
                | Q(follower=target, following=request.user)
            ).delete()
            blocked = True
            messages.success(request, f'@{target.username} заблокирован.')
    except (DatabaseError, OSError, PermissionError, IOError):
        messages.error(request, WRITE_ERROR_MSG)
        return redirect('vibel:profile', username=username)
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
    if next_url:
        return redirect(next_url)
    return redirect('vibel:profile', username=username)


@login_required
@require_POST
def report_content(request):
    form = ReportForm(request.POST)
    if not form.is_valid():
        err = None
        if form.errors.get('reason_other'):
            err = form.errors['reason_other'][0]
        elif form.errors.get('reason_choice'):
            err = form.errors['reason_choice'][0]
        elif form.non_field_errors():
            err = form.non_field_errors()[0]
        messages.error(request, err or 'Проверьте форму жалобы.')
        return redirect(request.POST.get('next') or 'vibel:feed')
    target_type = request.POST.get('target_type', '')
    target_id = request.POST.get('target_id', '')
    try:
        tid = int(target_id)
    except (TypeError, ValueError):
        messages.error(request, 'Некорректная цель жалобы.')
        return redirect('vibel:feed')
    if target_type not in (
        ContentReport.TARGET_POST,
        ContentReport.TARGET_COMMENT,
        ContentReport.TARGET_DM,
    ):
        messages.error(request, 'Некорректный тип жалобы.')
        return redirect('vibel:feed')
    try:
        ContentReport.objects.create(
            reporter=request.user,
            target_type=target_type,
            target_id=tid,
            reason=form.cleaned_data['reason'],
        )
    except (DatabaseError, OSError, PermissionError, IOError):
        return respond_write_error(request)
    messages.success(request, 'Жалоба отправлена. Спасибо.')
    return redirect(request.POST.get('next') or 'vibel:feed')


@login_required
@require_POST
def notification_mark_all_read(request):
    try:
        request.user.notifications.filter(is_read=False).update(is_read=True)
    except (DatabaseError, OSError, PermissionError, IOError):
        return respond_write_error(request, redirect_name='vibel:notifications')
    return redirect('vibel:notifications')


@login_required
@require_POST
def notification_mark_read(request, notification_id):
    n = get_object_or_404(
        Notification, id=notification_id, recipient=request.user
    )
    try:
        n.is_read = True
        n.save(update_fields=['is_read'])
    except (DatabaseError, OSError, PermissionError, IOError):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'ok': False, 'error': WRITE_ERROR_MSG}, status=500)
        return respond_write_error(request, redirect_name='vibel:notifications')
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'ok': True})
    return redirect('vibel:notifications')


@login_required
@require_POST
def dm_message_edit(request, username, message_id):
    other = get_object_or_404(User, username=username)
    if not are_friends(request.user, other):
        return redirect('vibel:messages_inbox')
    msg = get_object_or_404(
        DirectMessage,
        pk=message_id,
        sender=request.user,
        recipient=other,
    )
    if msg.hidden_for_sender_at:
        messages.error(request, 'Сообщение уже удалено.')
        return redirect('vibel:messages_thread', username=other.username)
    cutoff = timezone.now() - DM_EDIT_WINDOW
    if msg.created_at < cutoff:
        messages.error(request, 'Редактировать можно только 15 минут после отправки.')
        return redirect('vibel:messages_thread', username=other.username)
    body = (request.POST.get('body') or '').strip()
    if not body:
        messages.error(request, 'Текст не может быть пустым.')
        return redirect('vibel:messages_thread', username=other.username)
    try:
        msg.body = body
        msg.edited_at = timezone.now()
        msg.save(update_fields=['body', 'edited_at'])
    except (DatabaseError, OSError, PermissionError, IOError):
        messages.error(request, WRITE_ERROR_MSG)
        return redirect('vibel:messages_thread', username=other.username)
    messages.success(request, 'Сообщение изменено.')
    return redirect('vibel:messages_thread', username=other.username)
