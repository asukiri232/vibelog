from django import forms
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm as AuthPasswordChangeForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import Comment, Post, Profile
from .utils import optimize_uploaded_image


def _max_image_bytes():
    return int(getattr(settings, 'MAX_IMAGE_UPLOAD_BYTES', 8 * 1024 * 1024))


MAX_IMAGE_UPLOAD_BYTES = _max_image_bytes()
MAX_POST_IMAGES = 8
MAX_VIDEO_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 МБ


def files_getlist(files, key):
    if not files:
        return []
    if hasattr(files, 'getlist'):
        return files.getlist(key)
    val = files.get(key)
    if not val:
        return []
    if isinstance(val, (list, tuple)):
        return list(val)
    return [val]


class StyledAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Email или логин'
        self.fields['password'].label = 'Пароль'
        self.fields['username'].widget.attrs['class'] = 'vl-input'
        self.fields['username'].widget.attrs['autocomplete'] = 'username'
        self.fields['password'].widget.attrs['class'] = 'vl-input'
        self.fields['password'].widget.attrs['autocomplete'] = 'current-password'

    def get_invalid_login_error(self):
        err = super().get_invalid_login_error()
        if getattr(settings, 'VERCEL_EPHEMERAL_DB', False):
            return ValidationError(
                'Неверный логин или пароль. На демо-Vercel старый аккаунт мог уже стереться — '
                'зарегистрируйтесь заново или подключите Neon (см. инструкцию выше).',
                code='invalid_login',
            )
        return err


class RegisterForm(forms.Form):
    name = forms.CharField(
        label='Имя',
        max_length=80,
        strip=True,
        widget=forms.TextInput(
            attrs={
                'class': 'vl-input',
                'placeholder': 'Имя или имя и фамилия',
                'autocomplete': 'name',
            }
        ),
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(
            attrs={'class': 'vl-input', 'autocomplete': 'email'}
        ),
    )
    password = forms.CharField(
        label='Пароль',
        strip=False,
        widget=forms.PasswordInput(
            attrs={'class': 'vl-input', 'autocomplete': 'new-password'}
        ),
    )
    password_confirm = forms.CharField(
        label='Пароль ещё раз',
        strip=False,
        widget=forms.PasswordInput(
            attrs={'class': 'vl-input', 'autocomplete': 'new-password'}
        ),
    )

    def clean_name(self):
        name = (self.cleaned_data.get('name') or '').strip()
        if not name:
            raise ValidationError('Введите имя.')
        return name

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        max_u = User._meta.get_field('username').max_length
        uname = email[:max_u]
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('Этот email уже занят.')
        if User.objects.filter(username__iexact=uname).exists():
            raise ValidationError('Этот email уже занят.')
        return email

    def clean(self):
        data = super().clean()
        p1 = data.get('password')
        p2 = data.get('password_confirm')
        if p1 is not None and p2 is not None and p1 != p2:
            raise ValidationError('Пароли не совпадают.')
        return data

    def save(self):
        email = self.cleaned_data['email']
        max_u = User._meta.get_field('username').max_length
        uname = email[:max_u]
        user = User.objects.create_user(
            username=uname,
            email=email,
            password=self.cleaned_data['password'],
        )
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.display_name = self.cleaned_data['name']
        profile.save(update_fields=['display_name'])
        return user


class ProfileEditForm(forms.ModelForm):
    """FileField вместо ImageField — на Vercel нет Pillow, иначе 500 при загрузке."""

    class Meta:
        model = Profile
        fields = (
            'display_name',
            'bio',
            'location',
            'is_private',
        )
        labels = {
            'display_name': 'Имя',
            'bio': 'О себе',
            'location': 'Локация',
            'is_private': 'Закрытый профиль (посты только для подписчиков)',
        }
        widgets = {
            'display_name': forms.TextInput(attrs={'class': 'vl-input'}),
            'bio': forms.Textarea(attrs={'class': 'vl-input vl-textarea', 'rows': 4}),
            'location': forms.TextInput(attrs={'class': 'vl-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cover'] = forms.FileField(
            label='Обложка профиля',
            required=False,
            widget=forms.FileInput(
                attrs={
                    'class': 'vl-file-input',
                    'accept': 'image/*',
                }
            ),
        )
        self.fields['avatar'] = forms.FileField(
            label='Фото профиля',
            required=False,
            widget=forms.FileInput(
                attrs={
                    'class': 'vl-file-input vl-file-input--avatar',
                    'accept': 'image/*',
                    'data-vl-avatar-editor': '1',
                }
            ),
        )

    def _clean_profile_image(self, name):
        upload = self.files.get(name) if self.files else None
        if not upload:
            return None
        max_b = _max_image_bytes()
        if upload.size > max_b:
            mb = max(1, max_b // (1024 * 1024))
            raise ValidationError(f'Файл больше {mb} МБ.')
        return optimize_uploaded_image(upload)

    def clean_avatar(self):
        return self._clean_profile_image('avatar')

    def clean_cover(self):
        return self._clean_profile_image('cover')

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.files and self.files.get('avatar'):
            instance.avatar = self.cleaned_data['avatar']
        if self.files and self.files.get('cover'):
            instance.cover = self.cleaned_data['cover']
        if commit:
            instance.save()
        return instance


class PostForm(forms.ModelForm):
    # Важно: используем FileField (не ImageField) и валидируем сами.
    # Это позволяет принимать несколько файлов через input name="images" multiple,
    # а также не ломаться на нестандартных минимальных тестовых PNG.
    image = forms.FileField(
        label='Фотографии',
        required=False,
        widget=forms.ClearableFileInput(
            attrs={
                'class': 'vl-file-input',
                'accept': 'image/*',
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Эти поля нужны для UI обрезки, но не должны быть обязательными для фото-постов.
        self.fields['video_clip_limit_s'].required = False
        self.fields['video_clip_start_s'].required = False
        self.fields['video_clip_end_s'].required = False
        self.fields['video_clip_limit_s'].initial = (
            self.fields['video_clip_limit_s'].initial or 15
        )
        self.fields['video_clip_start_s'].initial = (
            self.fields['video_clip_start_s'].initial or 0
        )

    class Meta:
        model = Post
        fields = (
            'image',
            'video',
            'video_clip_limit_s',
            'video_clip_start_s',
            'video_clip_end_s',
            'caption',
            'category',
            'visibility',
        )
        labels = {
            'image': 'Фотографии',
            'video': 'Видео (клип)',
            'video_clip_limit_s': 'Длина клипа',
            'video_clip_start_s': 'Начало (сек)',
            'video_clip_end_s': 'Конец (сек)',
            'caption': 'Подпись',
            'category': 'Тип поста',
            'visibility': 'Видимость',
        }
        widgets = {
            'image': forms.FileInput(
                attrs={
                    'class': 'vl-file-input',
                    'accept': 'image/*',
                    # multiple field is rendered in template for correct name/getlist
                }
            ),
            'video': forms.FileInput(
                attrs={
                    'class': 'vl-file-input',
                    'accept': 'video/*',
                    'data-vl-clip-input': '1',
                }
            ),
            'video_clip_limit_s': forms.Select(
                attrs={
                    'class': 'vl-select',
                    'data-vl-clip-limit': '1',
                }
            ),
            'video_clip_start_s': forms.HiddenInput(
                attrs={
                    'data-vl-clip-start': '1',
                }
            ),
            'video_clip_end_s': forms.HiddenInput(
                attrs={
                    'data-vl-clip-end': '1',
                }
            ),
            'caption': forms.Textarea(attrs={'class': 'vl-input vl-textarea', 'rows': 3}),
            'category': forms.Select(attrs={'class': 'vl-select'}),
            'visibility': forms.Select(attrs={'class': 'vl-select'}),
        }

    def clean(self):
        data = super().clean()
        image = data.get('image')
        video = data.get('video')
        images = files_getlist(self.files, 'images')
        # Backward compat: if template still posts 'image' single file.
        if not images:
            images = files_getlist(self.files, 'image')
        if not images and image:
            images = [image]
        if not images:
            images = files_getlist(self.files, 'extra_images')

        if video and images:
            raise ValidationError('Выберите либо видео, либо фото.')
        if not video and not images and not (self.instance and self.instance.pk):
            raise ValidationError('Добавьте хотя бы одно фото или видео.')
        if len(images) > MAX_POST_IMAGES:
            raise ValidationError(f'Не больше {MAX_POST_IMAGES} фото.')
        self._images = images

        if video:
            if video.size > MAX_VIDEO_UPLOAD_BYTES:
                raise ValidationError('Видео слишком большое (максимум 50 МБ).')
            limit_s = int(data.get('video_clip_limit_s') or 15)
            start_s = int(data.get('video_clip_start_s') or 0)
            end_raw = data.get('video_clip_end_s')
            end_s = int(end_raw) if end_raw not in (None, '',) else None
            if start_s < 0:
                raise ValidationError('Начало клипа должно быть >= 0.')
            if end_s is not None and end_s <= start_s:
                raise ValidationError('Конец клипа должен быть больше начала.')
            if end_s is not None and end_s - start_s > limit_s:
                raise ValidationError(f'Клип должен быть не длиннее {limit_s} секунд.')
            data['video_clip_limit_s'] = limit_s
            data['video_clip_start_s'] = start_s
            data['video_clip_end_s'] = end_s
        return data

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            if image.size > MAX_IMAGE_UPLOAD_BYTES:
                raise ValidationError('Файл больше 8 МБ.')
            return optimize_uploaded_image(image)
        return image

    def save_extra_images(self, post):
        from .models import PostAttachment

        images = getattr(self, '_images', None) or (
            self.files.getlist('images') if self.files else []
        )
        # first goes to post.image (handled in save_post_with_form); rest become attachments
        for i, f in enumerate(images[1:], start=1):
            if not f:
                continue
            if f.size > MAX_IMAGE_UPLOAD_BYTES:
                continue
            PostAttachment.objects.create(
                post=post,
                image=optimize_uploaded_image(f),
                sort_order=i,
            )


class PostEditForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('caption', 'category', 'visibility')
        labels = PostForm.Meta.labels
        widgets = {
            'caption': forms.Textarea(attrs={'class': 'vl-input vl-textarea', 'rows': 3}),
            'category': forms.Select(attrs={'class': 'vl-select'}),
            'visibility': forms.Select(attrs={'class': 'vl-select'}),
        }


class PasswordChangeForm(AuthPasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('old_password', 'new_password1', 'new_password2'):
            self.fields[name].widget.attrs['class'] = 'vl-input'


class NotificationPrefsForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = (
            'notify_likes',
            'notify_comments',
            'notify_follows',
            'notify_mentions',
        )
        labels = {
            'notify_likes': 'Лайки на мои посты',
            'notify_comments': 'Комментарии',
            'notify_follows': 'Новые подписчики',
            'notify_mentions': 'Упоминания @логин',
        }


REPORT_REASON_CHOICES = [
    ('spam', 'Спам'),
    ('harassment', 'Оскорбления или травля'),
    ('inappropriate', 'Неприемлемый контент'),
    ('violence', 'Насилие или угрозы'),
    ('misinformation', 'Ложная информация'),
    ('copyright', 'Нарушение авторских прав'),
    ('other', 'Другое — указать своё'),
]


class ReportForm(forms.Form):
    reason_choice = forms.ChoiceField(
        label='Причина жалобы',
        choices=REPORT_REASON_CHOICES,
        widget=forms.RadioSelect,
        required=True,
    )
    reason_other = forms.CharField(
        label='Своя причина',
        max_length=500,
        required=False,
        widget=forms.Textarea(
            attrs={
                'class': 'vl-input vl-textarea',
                'rows': 3,
                'placeholder': 'Кратко опишите, что не так…',
            }
        ),
    )

    def clean(self):
        data = super().clean()
        choice = data.get('reason_choice')
        other = (data.get('reason_other') or '').strip()
        labels = dict(REPORT_REASON_CHOICES)

        if choice == 'other':
            if not other:
                self.add_error('reason_other', 'Укажите причину жалобы.')
            else:
                data['reason'] = other
        elif choice:
            data['reason'] = labels.get(choice, choice)
        else:
            raise ValidationError('Выберите причину жалобы.')
        return data


class AccountDeleteForm(forms.Form):
    password = forms.CharField(
        label='Текущий пароль',
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'vl-input', 'autocomplete': 'current-password'}),
    )
    confirm_text = forms.CharField(
        label='Введите DELETE для подтверждения',
        max_length=10,
        widget=forms.TextInput(attrs={'class': 'vl-input', 'autocomplete': 'off'}),
    )

    def clean_confirm_text(self):
        val = (self.cleaned_data.get('confirm_text') or '').strip()
        if val != 'DELETE':
            raise ValidationError('Введите слово DELETE заглавными буквами.')
        return val


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text', 'image')
        labels = {'text': 'Комментарий', 'image': ''}
        widgets = {
            'text': forms.Textarea(
                attrs={
                    'class': 'vl-input vl-textarea',
                    'rows': '1',
                    'placeholder': 'Оставить комментарий',
                    'maxlength': '500',
                    'autocomplete': 'off',
                    'data-comment-text': '',
                }
            ),
            'image': forms.FileInput(
                attrs={
                    'class': 'vl-attach-input',
                    'accept': 'image/*',
                    'aria-label': 'Прикрепить фото к комментарию',
                    'title': 'Прикрепить фото',
                    'data-comment-file': '',
                }
            ),
        }

    def clean(self):
        data = super().clean()
        text = (data.get('text') or '').strip()
        image = data.get('image')
        if not text and not image:
            raise ValidationError('Добавьте текст или изображение.')
        data['text'] = text
        return data

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image and image.size > MAX_IMAGE_UPLOAD_BYTES:
            raise ValidationError('Файл больше 8 МБ.')
        if image:
            return optimize_uploaded_image(image)
        return image


MAX_DM_IMAGES = 12


class DirectMessageForm(forms.Form):
    text = forms.CharField(
        label='',
        max_length=2000,
        required=False,
        strip=True,
        widget=forms.Textarea(
            attrs={
                'class': 'vl-input vl-textarea',
                'rows': 1,
                'placeholder': 'Текст или фото ниже…',
            }
        ),
    )

    def clean(self):
        data = super().clean()
        text = (data.get('text') or '').strip()
        raw_files = self.files.getlist('images')
        images = []
        for f in raw_files:
            if not f or not getattr(f, 'name', ''):
                continue
            if f.size > MAX_IMAGE_UPLOAD_BYTES:
                raise ValidationError('Каждый файл не больше 8 МБ.')
            ct = getattr(f, 'content_type', '') or ''
            if ct and not ct.startswith('image/'):
                raise ValidationError('Можно прикреплять только изображения.')
            images.append(f)
        if len(images) > MAX_DM_IMAGES:
            raise ValidationError(f'Не больше {MAX_DM_IMAGES} фото за раз.')
        if not text and not images:
            raise ValidationError('Напишите текст или прикрепите фото.')
        data['text'] = text
        data['images'] = images
        return data
