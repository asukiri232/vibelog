from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from vibel.forms import PostForm
from vibel.models import Category, Post, PostAttachment, Profile
from vibel.views_extended import save_post_with_form

MINIMAL_PNG = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
    b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f'
    b'\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
)


class PostAttachmentTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name='T', slug='t', order=0)
        self.user = User.objects.create_user(
            username='poster', email='p@e.com', password='pass12345'
        )
        Profile.objects.get_or_create(user=self.user)

    def test_save_main_and_extra_images(self):
        main = SimpleUploadedFile('main.png', MINIMAL_PNG, content_type='image/png')
        ex1 = SimpleUploadedFile('e1.png', MINIMAL_PNG, content_type='image/png')
        ex2 = SimpleUploadedFile('e2.png', MINIMAL_PNG, content_type='image/png')
        data = {
            'caption': 'test',
            'category': self.cat.pk,
            'visibility': Post.VIS_PUBLIC,
        }
        files = {'image': main, 'extra_images': [ex1, ex2]}
        form = PostForm(data, files)
        self.assertTrue(form.is_valid(), form.errors)
        post = save_post_with_form(form, self.user, files)
        self.assertTrue(post.image)
        self.assertEqual(post.attachments.count(), 2)

    def test_save_only_extra_images(self):
        ex1 = SimpleUploadedFile('e1.png', MINIMAL_PNG, content_type='image/png')
        ex2 = SimpleUploadedFile('e2.png', MINIMAL_PNG, content_type='image/png')
        data = {
            'caption': 'only extras',
            'category': self.cat.pk,
            'visibility': Post.VIS_PUBLIC,
        }
        files = {'extra_images': [ex1, ex2]}
        form = PostForm(data, files)
        self.assertTrue(form.is_valid(), form.errors)
        post = save_post_with_form(form, self.user, files)
        self.assertTrue(post.image)
        self.assertEqual(post.attachments.count(), 1)
