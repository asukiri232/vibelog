from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    name = models.CharField('название', max_length=64)
    slug = models.SlugField('URL-имя', unique=True)
    order = models.PositiveSmallIntegerField('порядок', default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'критерий'
        verbose_name_plural = 'критерии'

    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile', verbose_name='пользователь'
    )
    display_name = models.CharField('имя в ленте', max_length=80, blank=True)
    bio = models.TextField('о себе', max_length=500, blank=True)
    location = models.CharField('локация', max_length=120, blank=True)
    cover = models.ImageField('обложка', upload_to='covers/', blank=True, null=True)
    avatar = models.ImageField('аватар', upload_to='avatars/', blank=True, null=True)
    is_private = models.BooleanField('закрытый профиль', default=False)
    notify_likes = models.BooleanField('уведомления о лайках', default=True)
    notify_comments = models.BooleanField('уведомления о комментариях', default=True)
    notify_follows = models.BooleanField('уведомления о подписках', default=True)
    notify_mentions = models.BooleanField('уведомления об упоминаниях', default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'профиль'
        verbose_name_plural = 'профили'

    def __str__(self):
        return self.display_name or self.user.username

    def display_handle(self):
        return self.display_name or self.user.username


class Follow(models.Model):
    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following_set',
        verbose_name='подписчик',
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followers_set',
        verbose_name='на кого подписан',
    )
    created_at = models.DateTimeField('дата', auto_now_add=True)

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'подписки'
        unique_together = [['follower', 'following']]
        indexes = [
            models.Index(fields=['follower']),
            models.Index(fields=['following']),
        ]

    def __str__(self):
        return f'{self.follower} → {self.following}'


class Post(models.Model):
    VIS_PUBLIC = 'public'
    VIS_PRIVATE = 'private'
    VIS_DRAFT = 'draft'
    VISIBILITY_CHOICES = [
        (VIS_PUBLIC, 'Публичный'),
        (VIS_PRIVATE, 'Только для себя'),
        (VIS_DRAFT, 'Черновик'),
    ]

    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='posts', verbose_name='автор'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='posts',
        verbose_name='категория',
    )
    image = models.ImageField('изображение', upload_to='posts/', blank=True)
    video = models.FileField(
        'видео',
        upload_to='posts/video/',
        blank=True,
        null=True,
    )
    video_clip_start_s = models.PositiveIntegerField(
        'начало клипа (сек)',
        default=0,
    )
    video_clip_end_s = models.PositiveIntegerField(
        'конец клипа (сек)',
        blank=True,
        null=True,
    )
    video_clip_limit_s = models.PositiveSmallIntegerField(
        'лимит клипа (сек)',
        choices=[(15, '15 секунд'), (30, '30 секунд')],
        default=15,
    )
    caption = models.TextField('подпись', max_length=2200, blank=True)
    visibility = models.CharField(
        'видимость',
        max_length=16,
        choices=VISIBILITY_CHOICES,
        default=VIS_PUBLIC,
    )
    likes_count = models.PositiveIntegerField('лайков', default=0)
    created_at = models.DateTimeField('создан', auto_now_add=True)
    updated_at = models.DateTimeField('изменён', auto_now=True)

    class Meta:
        verbose_name = 'пост'
        verbose_name_plural = 'посты'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['-likes_count', '-created_at']),
        ]

    def __str__(self):
        who = self.author.username if self.author_id else '?'
        return f'Пост #{self.pk or "—"} ({who})'


class PostAttachment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name='пост',
    )
    image = models.ImageField('изображение', upload_to='posts/extra/')
    sort_order = models.PositiveSmallIntegerField('порядок', default=0)

    class Meta:
        verbose_name = 'доп. фото к посту'
        verbose_name_plural = 'доп. фото к постам'
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f'Фото к посту #{self.post_id}'


class Like(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='likes', verbose_name='пользователь'
    )
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name='likes', verbose_name='пост'
    )
    created_at = models.DateTimeField('дата', auto_now_add=True)

    class Meta:
        verbose_name = 'лайк'
        verbose_name_plural = 'лайки'
        unique_together = [['user', 'post']]
        indexes = [
            models.Index(fields=['post']),
        ]

    def __str__(self):
        return f'{self.user} ♥ пост #{self.post_id}'


class Comment(models.Model):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name='comments', verbose_name='пост'
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='comments', verbose_name='автор'
    )
    text = models.TextField('текст', max_length=500, blank=True, default='')
    image = models.ImageField(
        'изображение', upload_to='comments/', blank=True, null=True
    )
    created_at = models.DateTimeField('создан', auto_now_add=True)

    class Meta:
        verbose_name = 'комментарий'
        verbose_name_plural = 'комментарии'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['post', '-created_at']),
        ]

    def __str__(self):
        t = (self.text or '').strip()[:40]
        return f'Комментарий #{self.pk or "—"}: {t or "[фото]"}'


class SavedPost(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='saved_posts', verbose_name='пользователь'
    )
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name='saved_by', verbose_name='пост'
    )
    created_at = models.DateTimeField('дата', auto_now_add=True)

    class Meta:
        verbose_name = 'сохранённый пост'
        verbose_name_plural = 'сохранённые посты'
        unique_together = [['user', 'post']]
        indexes = [models.Index(fields=['user', '-created_at'])]

    def __str__(self):
        return f'{self.user} → пост #{self.post_id}'


class HiddenPost(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='hidden_posts', verbose_name='пользователь'
    )
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name='hidden_by', verbose_name='пост'
    )
    created_at = models.DateTimeField('дата', auto_now_add=True)

    class Meta:
        verbose_name = 'скрытый пост'
        verbose_name_plural = 'скрытые посты'
        unique_together = [['user', 'post']]

    def __str__(self):
        return f'{self.user} скрыл пост #{self.post_id}'


class UserBlock(models.Model):
    blocker = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='blocks_out',
        verbose_name='кто заблокировал',
    )
    blocked = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='blocks_in',
        verbose_name='кого заблокировали',
    )
    created_at = models.DateTimeField('дата', auto_now_add=True)

    class Meta:
        verbose_name = 'блокировка'
        verbose_name_plural = 'блокировки'
        unique_together = [['blocker', 'blocked']]

    def __str__(self):
        return f'{self.blocker} ⊗ {self.blocked}'


class ContentReport(models.Model):
    TARGET_POST = 'post'
    TARGET_COMMENT = 'comment'
    TARGET_DM = 'dm'
    TARGET_CHOICES = [
        (TARGET_POST, 'Пост'),
        (TARGET_COMMENT, 'Комментарий'),
        (TARGET_DM, 'Сообщение'),
    ]

    reporter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reports_sent',
        verbose_name='отправитель',
    )
    target_type = models.CharField('тип объекта', max_length=16, choices=TARGET_CHOICES)
    target_id = models.PositiveIntegerField('ID объекта')
    reason = models.CharField('причина', max_length=500, blank=True)
    created_at = models.DateTimeField('дата', auto_now_add=True)

    class Meta:
        verbose_name = 'жалоба'
        verbose_name_plural = 'жалобы'
        indexes = [models.Index(fields=['target_type', 'target_id'])]

    def __str__(self):
        return f'Жалоба #{self.pk or "—"} ({self.get_target_type_display()})'


class DirectMessage(models.Model):
    """Личные сообщения только между пользователями с взаимной подпиской (друзья)."""
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='dm_sent', verbose_name='отправитель'
    )
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='dm_received',
        verbose_name='получатель',
    )
    body = models.TextField('текст', max_length=2000, blank=True, default='')
    image = models.ImageField(
        'изображение', upload_to='dm/', blank=True, null=True
    )
    read_at = models.DateTimeField('прочитано', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    hidden_for_sender_at = models.DateTimeField(
        'скрыто у отправителя', null=True, blank=True
    )
    hidden_for_recipient_at = models.DateTimeField(
        'скрыто у получателя', null=True, blank=True
    )
    reply_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name='ответ на',
    )
    edited_at = models.DateTimeField('изменено', null=True, blank=True)

    class Meta:
        verbose_name = 'личное сообщение'
        verbose_name_plural = 'личные сообщения'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['recipient', 'read_at']),
            models.Index(fields=['sender', 'recipient', '-created_at']),
        ]

    def __str__(self):
        if self.body:
            piece = self.body[:40]
        elif self.image or (self.pk and self.attachments.exists()):
            piece = '[фото]'
        else:
            piece = ''
        return f'{self.sender_id}→{self.recipient_id}: {piece}'


class DirectMessageAttachment(models.Model):
    message = models.ForeignKey(
        DirectMessage,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name='сообщение',
    )
    image = models.ImageField('изображение', upload_to='dm/')
    sort_order = models.PositiveSmallIntegerField('порядок', default=0)

    class Meta:
        verbose_name = 'вложение к сообщению'
        verbose_name_plural = 'вложения к сообщениям'
        ordering = ['sort_order', 'id']


class Notification(models.Model):
    TYPE_LIKE = 'like'
    TYPE_COMMENT = 'comment'
    TYPE_FOLLOW = 'follow'
    TYPE_MENTION = 'mention'
    TYPE_CHOICES = [
        (TYPE_LIKE, 'Лайк'),
        (TYPE_COMMENT, 'Комментарий'),
        (TYPE_FOLLOW, 'Подписка'),
        (TYPE_MENTION, 'Упоминание'),
    ]

    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='получатель',
    )
    actor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications_sent',
        verbose_name='инициатор',
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name='пост',
    )
    event_type = models.CharField('тип', max_length=16, choices=TYPE_CHOICES)
    text = models.CharField('текст', max_length=180, blank=True)
    is_read = models.BooleanField('прочитано', default=False)
    created_at = models.DateTimeField('дата', auto_now_add=True)

    class Meta:
        verbose_name = 'уведомление'
        verbose_name_plural = 'уведомления'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read', '-created_at']),
        ]

    def __str__(self):
        return f'{self.get_event_type_display()} → {self.recipient}'
