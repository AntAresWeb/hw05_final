import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from mixer.backend.django import mixer

from posts.models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TestForms(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = mixer.blend(User, username='RingoStarr')
        cls.group = mixer.blend(Group, slug='test-slug')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self) -> None:
        self.auth = Client()
        self.auth.force_login(mixer.blend(User, username='auth'))
        self.author = Client()
        self.author.force_login(TestForms.user)

    def test_create_post_new_record(self):
        '''Проверка создания новой записи в базе данных.'''
        Post.objects.all().delete()
        posts_number = Post.objects.count()
        self.auth.post(
            reverse('posts:post_create'),
            data={
                'text': 'Тестовое сообщение',
                'group': TestForms.group.id,
            },
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_number + 1)

    def test_edit_post_of_author_at_id(self):
        '''Проверка изменения указанного по id поста.'''
        mixer.blend(Post, author=TestForms.user, group=TestForms.group)
        post_old = Post.objects.get(id=1)
        form_data = {
            'text': 'Изменение сообщения тестом',
            'group': TestForms.group.id,
        }
        self.author.post(
            reverse('posts:post_edit', kwargs={'post_id': 1}),
            data=form_data,
            follow=True
        )
        post_new = Post.objects.get(id=1)
        self.assertEqual(post_new.text, form_data['text'])
        self.assertNotEqual(post_new.text, post_old.text)

    def test_presence_image_on_create_post(self):
        """
        Проверка, что при отправке поста с картинкой через форму
        PostForm создаётся запись в базе данных.
        """
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый заголовок',
            'group': self.group.id,
            'image': uploaded,
        }
        old_set = set(Post.objects.all())
        self.auth.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        new_set = set(Post.objects.all()).difference(old_set)
        if len(new_set) > 0:
            post = list(new_set)
            self.assertTrue(
                post[0].image,
                msg='Созданная новая запись не содержит картинку'
            )
        else:
            self.assertEqual(len(new_set), 1,
                             msg='Запись в базе данных не создалась.')
