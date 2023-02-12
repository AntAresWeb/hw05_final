from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase
from mixer.backend.django import mixer

from posts.models import Group, Post, User


class TestURLs(TestCase):
    '''Проверка доступности страниц приложения posts.'''

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = mixer.blend(User, username='RingoStarr')
        cls.group = mixer.blend(Group, slug='test-slug')
        cls.post = mixer.blend(Post, id=1, author=cls.user, group=cls.group)
        cls.public_urls = (
            ('/', 'posts/index.html',),
            (f'/group/{cls.group.slug}/', 'posts/group_list.html',),
            (f'/profile/{cls.user}/', 'posts/profile.html',),
            (f'/posts/{cls.post.id}/', 'posts/post_detail.html',),
        )
        cls.private_urls = (
            ('/create/', 'posts/create_post.html',),
        )
        cls.author_urls = (
            (f'/posts/{cls.post.id}/edit/', 'posts/create_post.html',),
        )
        cls.non_existen_address = '/non-existent-address/'

    def setUp(self):
        self.anon = Client()
        self.auth = Client()
        self.auth.force_login(mixer.blend(User, username='auth'))
        self.author = Client()
        self.author.force_login(self.user)
        cache.clear()

    def test_urls_exists_at_desired_location(self):
        '''Проверка доступности пользователям адресов в приложении posts.'''
        for address, _ in self.public_urls:
            with self.subTest(address=address):
                self.assertEqual(
                    self.anon.get(address).status_code,
                    HTTPStatus.OK, msg='Анонимный пользователь.'
                )
                self.assertEqual(
                    self.auth.get(address).status_code,
                    HTTPStatus.OK, msg='Авторизованный пользователь.'
                )
                self.assertEqual(
                    self.author.get(address).status_code,
                    HTTPStatus.OK, msg='Пользователь - автор поста.'
                )
        for address, _ in self.private_urls:
            with self.subTest(address=address):
                self.assertEqual(
                    self.anon.get(address).status_code,
                    HTTPStatus.FOUND, msg='Анонимный пользователь.'
                )
                self.assertEqual(
                    self.auth.get(address).status_code,
                    HTTPStatus.OK, msg='Авторизованный пользователь.'
                )
                self.assertEqual(
                    self.author.get(address).status_code,
                    HTTPStatus.OK, msg='Пользователь - автор поста.'
                )
        for address, _ in self.author_urls:
            with self.subTest(address=address):
                self.assertEqual(
                    self.anon.get(address).status_code,
                    HTTPStatus.FOUND, msg='Анонимный пользователь.'
                )
                self.assertEqual(
                    self.auth.get(address).status_code,
                    HTTPStatus.FOUND, msg='Авторизованный пользователь.'
                )
                self.assertEqual(
                    self.author.get(address).status_code,
                    HTTPStatus.OK, msg='Пользователь - автор поста.'
                )
        address = self.non_existen_address
        with self.subTest(address=address):
            self.assertEqual(
                self.anon.get(address).status_code,
                HTTPStatus.NOT_FOUND, msg='Анонимный пользователь.'
            )
            self.assertEqual(
                self.auth.get(address).status_code,
                HTTPStatus.NOT_FOUND, msg='Авторизованный пользователь.'
            )
            self.assertEqual(
                self.author.get(address).status_code,
                HTTPStatus.NOT_FOUND, msg='Пользователь - автор поста.'
            )

    def test_urls_uses_correct_template(self):
        '''Проверка наличия шаблонов в приложении posts.'''
        address_templates = (
            self.public_urls + self.private_urls + self.author_urls)
        for address, template in address_templates:
            with self.subTest(address=address, template=template):
                response = self.author.get(address)
                self.assertTemplateUsed(response, template)
