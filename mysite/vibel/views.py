from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import CharField, Count, F, Q, Value
from django.db.models.functions import Coalesce, NullIf
from django.http import HttpResponseForbidden, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    CommentForm,
    DirectMessageForm,
    PostForm,
    ProfileEditForm,
    RegisterForm,
)
from .friends import are_friends, mutual_follow_ids
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
from .services import create_notification, notify_mentions
from .utils import blocked_user_ids, optimize_uploaded_image
from .views_extended import (
    DM_EDIT_WINDOW,
    block_toggle,
    dm_hidden_for_viewer,
    dm_message_edit,
    feed_queryset,
    hide_post_toggle,
    notification_mark_read,
    notification_mark_all_read,
    paginate_feed,
    post_delete,
    post_edit,
    report_content,
    save_post_with_form,
    settings_page,
)


def _wants_json_response(request):
    """Ответ JSON для AJAX: query (?vl_json=1) не теряется при multipart, плюс POST/заголовки."""

    if request.GET.get('vl_json') == '1':
        return True
    if request.POST.get('vl_expect_json') == '1':
        return True
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return True
    accept = (request.headers.get('accept') or '').lower()
    return 'application/json' in accept



def help_page(request):
    return render(request, 'vibel/help.html')


def feed(request):
    tab = request.GET.get('tab')
    if not tab:
        tab = 'popular'
    cat_slug = request.GET.get('category') or ''
    try:
        page = int(request.GET.get('page') or 1)
    except ValueError:
        page = 1

    qs = feed_queryset(request, tab, cat_slug)
    posts, has_more, page = paginate_feed(qs, page)

    if tab == 'following' and not request.user.is_authenticated:
        tab = 'popular'

    post_ids = [p.id for p in posts]
    liked_ids = set()
    if request.user.is_authenticated and post_ids:
        liked_ids = set(
            Like.objects.filter(user=request.user, post_id__in=post_ids).values_list(
                'post_id', flat=True
            )
        )
    saved_ids = set()
    if request.user.is_authenticated and post_ids:
        saved_ids = set(
            SavedPost.objects.filter(user=request.user, post_id__in=post_ids).values_list(
                'post_id', flat=True
            )
        )

    categories = Category.objects.all()
    comments_by_post = {post_id: [] for post_id in post_ids}
    if post_ids:
        for comment in (
            Comment.objects.select_related('author', 'author__profile')
            .filter(post_id__in=post_ids)
            .order_by('-created_at')[:200]
        ):
            arr = comments_by_post[comment.post_id]
            if len(arr) < 2:
                arr.append(comment)

    for post in posts:
        post.preview_comments = comments_by_post.get(post.id, [])
    comment_counts = dict(
        Comment.objects.filter(post_id__in=post_ids)
        .values_list('post_id')
        .annotate(total=Count('id'))
    )
    for post in posts:
        post.comments_total = comment_counts.get(post.id, 0)

    return render(
        request,
        'vibel/feed.html',
        {
            'posts': posts,
            'tab': tab,
            'categories': categories,
            'category_slug': cat_slug or '',
            'liked_ids': liked_ids,
            'saved_ids': saved_ids,
            'comment_form': CommentForm(),
            'feed_page': page,
            'feed_has_more': has_more,
        },
    )


@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = save_post_with_form(form, request.user, request.FILES)
            if post.visibility == Post.VIS_DRAFT:
                messages.success(request, 'Черновик сохранён.')
            else:
                messages.success(request, 'Пост опубликован.')
            return redirect('vibel:feed')
    else:
        form = PostForm()
    return render(request, 'vibel/post_form.html', {'form': form})


def profile_view(request, username):
    user = get_object_or_404(User, username=username)
    profile, _ = Profile.objects.get_or_create(user=user)
    posts = (
        user.posts.select_related('category')
        .prefetch_related('attachments')
        .order_by('-created_at')[:36]
    )
    posts_count = user.posts.count()
    is_following = False
    they_follow_me = False
    is_friend = False
    is_blocked = False
    blocked_by_me = False
    if request.user.is_authenticated and request.user != user:
        is_following = Follow.objects.filter(
            follower=request.user, following=user
        ).exists()
        they_follow_me = Follow.objects.filter(
            follower=user, following=request.user
        ).exists()
        is_friend = is_following and they_follow_me
        blocked_by_me = UserBlock.objects.filter(
            blocker=request.user, blocked=user
        ).exists()
        is_blocked = blocked_by_me or UserBlock.objects.filter(
            blocker=user, blocked=request.user
        ).exists()
    followers_n = user.followers_set.count()
    following_n = user.following_set.count()
    return render(
        request,
        'vibel/profile.html',
        {
            'profile_user': user,
            'profile': profile,
            'posts': posts,
            'posts_count': posts_count,
            'is_following': is_following,
            'they_follow_me': they_follow_me,
            'is_friend': is_friend,
            'is_blocked': is_blocked,
            'blocked_by_me': blocked_by_me,
            'followers_n': followers_n,
            'following_n': following_n,
        },
    )


@login_required
def profile_edit(request, username):
    user = get_object_or_404(User, username=username)
    if user != request.user:
        return HttpResponseForbidden()
    profile = user.profile
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('vibel:profile', username=user.username)
    else:
        form = ProfileEditForm(instance=profile)
    return render(
        request,
        'vibel/profile_edit.html',
        {'form': form, 'profile': profile},
    )


@login_required
@require_POST
def follow_toggle(request, username):
    target = get_object_or_404(User, username=username)
    if target == request.user:
        return redirect('vibel:profile', username=username)
    if UserBlock.objects.filter(
        Q(blocker=request.user, blocked=target)
        | Q(blocker=target, blocked=request.user)
    ).exists():
        messages.error(request, 'Действие недоступно из-за блокировки.')
        return redirect('vibel:profile', username=username)
    rel = Follow.objects.filter(follower=request.user, following=target)
    if rel.exists():
        rel.delete()
        messages.info(request, f'Вы отписались от @{target.username}')
    else:
        Follow.objects.create(follower=request.user, following=target)
        create_notification(
            recipient=target,
            actor=request.user,
            event_type=Notification.TYPE_FOLLOW,
            text=f'{request.user.username} подписался(ась) на вас',
        )
        if Follow.objects.filter(follower=target, following=request.user).exists():
            messages.success(
                request,
                f'Вы подписались на @{target.username}. Вы друзья — можно писать в разделе «Сообщения».',
            )
        else:
            messages.success(request, f'Вы подписались на @{target.username}')
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
    if next_url:
        return redirect(next_url)
    return redirect('vibel:profile', username=username)


@login_required
@require_POST
def like_toggle(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    like, created = Like.objects.get_or_create(user=request.user, post=post)
    if not created:
        like.delete()
        Notification.objects.filter(
            recipient=post.author,
            actor=request.user,
            post=post,
            event_type=Notification.TYPE_LIKE,
        ).delete()
    elif post.author_id != request.user.id:
        create_notification(
            recipient=post.author,
            actor=request.user,
            post=post,
            event_type=Notification.TYPE_LIKE,
            text=f'{request.user.username} поставил(а) лайк вашему посту',
        )
    likes_count = Like.objects.filter(post=post).count()
    Post.objects.filter(pk=post.pk).update(likes_count=likes_count)
    liked = created

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse(
            {
                'ok': True,
                'liked': liked,
                'likes_count': likes_count,
            }
        )

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
    if next_url:
        return redirect(next_url)
    return redirect('vibel:feed')


@login_required
@require_POST
def comment_create(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST, request.FILES)
    if form.is_valid():
        text_stripped = (form.cleaned_data.get('text') or '').strip()
        upload_image = form.cleaned_data.get('image')
        recent_cutoff = timezone.now() - timedelta(seconds=5)
        duplicate = None
        if not upload_image:
            duplicate = (
                Comment.objects.filter(
                    post=post,
                    author=request.user,
                    text=text_stripped,
                    created_at__gte=recent_cutoff,
                )
                .filter(Q(image='') | Q(image__isnull=True))
                .order_by('-created_at')
                .first()
            )
        else:
            cand = (
                Comment.objects.filter(
                    post=post,
                    author=request.user,
                    created_at__gte=recent_cutoff,
                )
                .exclude(Q(image='') | Q(image__isnull=True))
                .order_by('-created_at')
                .first()
            )
            if cand:
                try:
                    dup_sz = cand.image.size
                except OSError:
                    dup_sz = None
                up_sz = getattr(upload_image, 'size', None)
                if dup_sz is not None and up_sz is not None and dup_sz == up_sz:
                    duplicate = cand

        reused_existing = bool(duplicate)
        if duplicate:
            comment = duplicate
        else:
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
            if post.author_id != request.user.id:
                create_notification(
                    recipient=post.author,
                    actor=request.user,
                    post=post,
                    event_type=Notification.TYPE_COMMENT,
                    text=f'{request.user.profile.display_handle} прокомментировал(а) ваш пост',
                )
            notify_mentions(text=text_stripped, actor=request.user, post=post)
        if _wants_json_response(request):
            image_url = ''
            if comment.image:
                image_url = request.build_absolute_uri(comment.image.url)
            return JsonResponse(
                {
                    'ok': True,
                    'duplicate': reused_existing,
                    'comment': {
                        'id': comment.id,
                        'text': comment.text,
                        'image_url': image_url,
                        'author_username': comment.author.username,
                        'author_display': comment.author.profile.display_handle,
                        'delete_url': reverse(
                            'vibel:comment_delete',
                            kwargs={'post_id': post.id, 'comment_id': comment.id},
                        ),
                    },
                }
            )
    elif _wants_json_response(request):
        err_msg = 'Некорректный комментарий'
        if form.non_field_errors():
            err_msg = form.non_field_errors()[0]
        else:
            for errs in form.errors.values():
                if errs:
                    err_msg = errs[0]
                    break
        return JsonResponse({'ok': False, 'error': err_msg}, status=400)

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
    if next_url:
        return HttpResponseRedirect(next_url, status=303)
    return HttpResponseRedirect(reverse('vibel:feed'), status=303)


@login_required
@require_POST
def comment_delete(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, post_id=post_id)
    if comment.author_id != request.user.id and comment.post.author_id != request.user.id:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'ok': False, 'error': 'Нет прав'}, status=403)
        return HttpResponseForbidden()
    if comment.image:
        comment.image.delete(save=False)
    comment.delete()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'ok': True, 'comment_id': comment_id})
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
    if next_url:
        return redirect(next_url)
    return redirect('vibel:post_detail', post_id=post_id)


def register(request):
    if request.user.is_authenticated:
        return redirect('vibel:feed')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
            except DjangoValidationError as exc:
                msgs = getattr(exc, 'messages', None) or [str(exc)]
                for msg in msgs:
                    form.add_error('password', msg)
            else:
                login(request, user)
                return redirect('vibel:feed')
    else:
        form = RegisterForm()
    return render(request, 'vibel/register.html', {'form': form})


def _user_search_queryset(q):
    """Поиск: имя отображения в ленте (или логин, если имя пустое — как display_handle), логин, имя/фамилия, email."""

    q = (q or '').strip()
    if not q:
        return User.objects.none()
    return (
        User.objects.select_related('profile')
        .annotate(
            _display_handle=Coalesce(
                NullIf(F('profile__display_name'), Value('')),
                F('username'),
                output_field=CharField(max_length=200),
            )
        )
        .filter(
            Q(_display_handle__icontains=q)
            | Q(username__icontains=q)
            | Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(email__icontains=q)
        )
        .distinct()
        .order_by('username')
    )


def _materialize_users_in_search_order(user_ids):
    """Гарантирует строку Profile и возвращает User в том же порядке, что user_ids."""

    if not user_ids:
        return []
    for uid in user_ids:
        Profile.objects.get_or_create(user_id=uid)
    user_map = {
        u.pk: u
        for u in User.objects.select_related('profile').filter(pk__in=user_ids)
    }
    return [user_map[i] for i in user_ids if i in user_map]


def user_search(request):
    q = (request.GET.get('q') or '').strip()
    users = []
    if q:
        qs = _user_search_queryset(q)[:24]
        user_ids = list(qs.values_list('pk', flat=True))
        users = _materialize_users_in_search_order(user_ids)
    return render(request, 'vibel/user_search.html', {'q': q, 'users': users})


def user_search_api(request):
    q = (request.GET.get('q') or '').strip()
    if not q:
        return JsonResponse({'ok': True, 'items': []})

    qs = _user_search_queryset(q)[:8]
    user_ids = list(qs.values_list('pk', flat=True))
    users = _materialize_users_in_search_order(user_ids)
    items = []
    for user in users:
        profile = user.profile
        avatar = ''
        if profile.avatar:
            avatar = profile.avatar.url
        items.append(
            {
                'username': user.username,
                'display_name': profile.display_handle(),
                'profile_url': reverse('vibel:profile', kwargs={'username': user.username}),
                'avatar_url': avatar,
            }
        )
    return JsonResponse({'ok': True, 'items': items})


def post_detail(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related('author', 'author__profile', 'category').prefetch_related(
            'attachments'
        ),
        id=post_id,
    )
    comments = post.comments.select_related('author', 'author__profile').order_by(
        '-created_at'
    )
    liked = False
    saved = False
    if request.user.is_authenticated:
        liked = Like.objects.filter(user=request.user, post=post).exists()
        saved = SavedPost.objects.filter(user=request.user, post=post).exists()
    ctx = {
        'post': post,
        'comments': comments,
        'liked': liked,
        'saved': saved,
    }
    if request.user.is_authenticated:
        ctx['comment_form'] = CommentForm()
    return render(request, 'vibel/post_detail.html', ctx)


@login_required
def saved_posts(request):
    posts = (
        Post.objects.select_related('author', 'author__profile', 'category')
        .filter(saved_by__user=request.user)
        .order_by('-saved_by__created_at')[:80]
    )
    return render(request, 'vibel/saved_posts.html', {'posts': posts})


@login_required
@require_POST
def save_toggle(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    saved, created = SavedPost.objects.get_or_create(user=request.user, post=post)
    is_saved = created
    if not created:
        saved.delete()
        is_saved = False
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'ok': True, 'saved': is_saved})
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
    if next_url:
        return redirect(next_url)
    return redirect('vibel:feed')


@login_required
def notifications_list(request):
    notifications = request.user.notifications.select_related(
        'actor', 'actor__profile', 'post'
    )[:80]
    unread_count = request.user.notifications.filter(is_read=False).count()
    return render(
        request,
        'vibel/notifications.html',
        {'notifications': notifications, 'unread_count': unread_count},
    )


def _dm_visible_for_user(dm, user):
    """Для превью в списке диалогов — скрытые не показываем."""
    return not dm_hidden_for_viewer(dm, user)


@login_required
def messages_inbox(request):
    friend_ids = mutual_follow_ids(request.user)
    friends = list(
        User.objects.filter(id__in=friend_ids).select_related('profile').order_by('username')
    )
    last_by_other = {}
    if friend_ids:
        recent = (
            DirectMessage.objects.filter(
                Q(sender=request.user, recipient_id__in=friend_ids)
                | Q(recipient=request.user, sender_id__in=friend_ids)
            )
            .select_related('sender', 'recipient', 'sender__profile', 'recipient__profile')
            .prefetch_related('attachments')
            .order_by('-created_at')[:400]
        )
        for msg in recent:
            oid = msg.sender_id if msg.recipient_id == request.user.id else msg.recipient_id
            if oid not in friend_ids or oid in last_by_other:
                continue
            if not _dm_visible_for_user(msg, request.user):
                continue
            last_by_other[oid] = msg
    threads = []
    for f in friends:
        unread = DirectMessage.objects.filter(
            sender=f, recipient=request.user, read_at__isnull=True
        ).count()
        threads.append({'other': f, 'last': last_by_other.get(f.id), 'unread': unread})
    threads.sort(
        key=lambda t: -t['last'].created_at.timestamp() if t['last'] else float('inf')
    )
    return render(request, 'vibel/messages_inbox.html', {'threads': threads})


@login_required
def messages_thread(request, username):
    other = get_object_or_404(User.objects.select_related('profile'), username=username)
    if other.id == request.user.id:
        return redirect('vibel:messages_inbox')
    if UserBlock.objects.filter(
        Q(blocker=request.user, blocked=other)
        | Q(blocker=other, blocked=request.user)
    ).exists():
        messages.error(request, 'Переписка недоступна из-за блокировки.')
        return redirect('vibel:messages_inbox')
    if not are_friends(request.user, other):
        messages.error(
            request,
            'Писать можно только друзьям: нужна взаимная подписка (вы оба подписаны друг на друга).',
        )
        return redirect('vibel:messages_inbox')
    DirectMessage.objects.filter(
        sender=other, recipient=request.user, read_at__isnull=True
    ).update(read_at=timezone.now())
    if request.method == 'POST':
        form = DirectMessageForm(request.POST, request.FILES)
        if form.is_valid():
            imgs = form.cleaned_data.get('images') or []
            reply_to = None
            reply_raw = (request.POST.get('reply_to') or '').strip()
            if reply_raw:
                try:
                    reply_pk = int(reply_raw)
                except (TypeError, ValueError):
                    reply_pk = None
                if reply_pk:
                    reply_to = (
                        DirectMessage.objects.filter(pk=reply_pk)
                        .filter(
                            Q(sender=request.user, recipient=other)
                            | Q(sender=other, recipient=request.user)
                        )
                        .first()
                    )
            dm = DirectMessage.objects.create(
                sender=request.user,
                recipient=other,
                body=form.cleaned_data['text'],
                reply_to=reply_to,
            )
            for i, f in enumerate(imgs):
                DirectMessageAttachment.objects.create(
                    message=dm,
                    image=optimize_uploaded_image(f),
                    sort_order=i,
                )
            return redirect('vibel:messages_thread', username=other.username)
    else:
        form = DirectMessageForm()
    thread_messages = (
        DirectMessage.objects.filter(
            Q(sender=request.user, recipient=other)
            | Q(sender=other, recipient=request.user)
        )
        .select_related(
            'sender',
            'sender__profile',
            'reply_to',
            'reply_to__sender',
            'reply_to__sender__profile',
        )
        .prefetch_related('attachments', 'reply_to__attachments')
        .order_by('created_at')[:500]
    )
    for m in thread_messages:
        m.is_hidden_for_me = dm_hidden_for_viewer(m, request.user)
        m.show_reply_to = bool(
            m.reply_to_id
            and m.reply_to
            and not dm_hidden_for_viewer(m.reply_to, request.user)
        )
        m.can_edit = (
            m.sender_id == request.user.id
            and not m.is_hidden_for_me
            and m.created_at >= timezone.now() - DM_EDIT_WINDOW
            and not list(m.attachments.all())
            and not m.image
        )
    return render(
        request,
        'vibel/messages_thread.html',
        {
            'other': other,
            'thread_messages': thread_messages,
            'form': form,
            'dm_edit_window_minutes': int(DM_EDIT_WINDOW.total_seconds() // 60),
        },
    )


@login_required
@require_POST
def dm_message_delete(request, username, message_id):
    other = get_object_or_404(User.objects.select_related('profile'), username=username)
    if other.id == request.user.id:
        return redirect('vibel:messages_inbox')
    if not are_friends(request.user, other):
        messages.error(
            request,
            'Писать можно только друзьям: нужна взаимная подписка (вы оба подписаны друг на друга).',
        )
        return redirect('vibel:messages_inbox')
    msg = get_object_or_404(
        DirectMessage.objects.filter(
            Q(sender=request.user, recipient=other)
            | Q(sender=other, recipient=request.user)
        ),
        pk=message_id,
    )
    mode = (request.POST.get('mode') or 'me').strip().lower()
    if mode == 'all':
        if msg.sender_id != request.user.id:
            messages.error(request, 'Удалить у всех может только отправитель.')
        else:
            msg.delete()
            messages.success(request, 'Сообщение удалено у всех.')
        return redirect('vibel:messages_thread', username=other.username)

    now = timezone.now()
    if msg.sender_id == request.user.id:
        msg.hidden_for_sender_at = now
        msg.save(update_fields=['hidden_for_sender_at'])
    else:
        msg.hidden_for_recipient_at = now
        msg.save(update_fields=['hidden_for_recipient_at'])
    msg.refresh_from_db()
    if msg.hidden_for_sender_at and msg.hidden_for_recipient_at:
        msg.delete()
    messages.success(request, 'Сообщение скрыто у вас в этом чате.')
    return redirect('vibel:messages_thread', username=other.username)
