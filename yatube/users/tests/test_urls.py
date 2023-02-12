from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

User = get_user_model()


class TestUsersURLs(TestCase):
    '''Проверка доступности страниц приложения users.'''

    def setUp(self):
        # Создаем неавторизованного посетителя
        self.guest_client = Client()
        # Создаем авторизованного посетителя
        self.user = User.objects.create_user(username='auth')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_exists_at_desired_location(self):
        '''Проверка доступности адресов в приложении users.'''
        urls = {
            '/auth/signup/': [HTTPStatus.OK] * 2,
            '/auth/logout/': [HTTPStatus.OK] * 2,
            '/auth/login/': [HTTPStatus.OK] * 2,
            '/auth/password_change/': [HTTPStatus.FOUND] * 2,
            '/auth/password_change/done/': [HTTPStatus.FOUND] * 2,
            '/unexisting_page/': [HTTPStatus.NOT_FOUND] * 2,
        }
        for address, code in urls.items():
            # Не авторизованный посетитель.
            with self.subTest(address=address):
                '''Не авторизованный посетитель.'''
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, code[0],
                                 msg='Неавторизованный посетитель.')
            # Авторизованный посетитель.
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, code[1],
                                 msg='Авторизованный посетитель.')

    def test_urls_uses_correct_template(self):
        '''Проверка наличия шаблонов в приложении users.'''
        address_templates = {
            '/auth/login/': 'users/login.html',
            '/auth/logout/': 'users/logged_out.html',
            '/auth/signup/': 'users/signup.html',
        }
        for address, template in address_templates.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
