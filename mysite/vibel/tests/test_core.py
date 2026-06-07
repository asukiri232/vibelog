from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from vibel.models import Category, Post, Profile


class CoreFlowTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name='Test', slug='test', order=0)
        self.user = User.objects.create_user(
            username='tester', email='t@example.com', password='pass12345'
        )
        Profile.objects.get_or_create(user=self.user)

    def test_feed_loads(self):
        r = Client().get(reverse('vibel:feed'))
        self.assertEqual(r.status_code, 200)

    def test_settings_requires_login(self):
        r = Client().get(reverse('vibel:settings'))
        self.assertEqual(r.status_code, 302)

    def test_post_delete_own(self):
        post = Post.objects.create(
            author=self.user,
            category=self.cat,
            caption='x',
            visibility=Post.VIS_PUBLIC,
        )
        c = Client()
        c.login(username='tester', password='pass12345')
        r = c.post(reverse('vibel:post_delete', kwargs={'post_id': post.id}))
        self.assertEqual(r.status_code, 302)
        self.assertFalse(Post.objects.filter(pk=post.id).exists())
