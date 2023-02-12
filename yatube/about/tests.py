from django.contrib.auth import get_user_model
from django.test import Client, TestCase

User = get_user_model()


class StaticPagesURLTests(TestCase):
    '''Проверяем доступность статических страниц.'''
    def setUp(self):
        self.guest_client = Client()

    def test_url_exists_at_desired_location(self):
        '''Проверка доступности адресов в приложении about.'''
        urls = [
            '/about/tech/',
            '/about/author/',
        ]
        for address in urls:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, 200)

    def test_url_uses_correct_template(self):
        '''Проверка наличия шаблонов в приложении about.'''
        address_templates = {
            '/about/tech/': 'about/tech.html',
            '/about/author/': 'about/author.html',
        }
        for address, template in address_templates.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)
