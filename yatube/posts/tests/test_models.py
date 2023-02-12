from django.test import TestCase
from mixer.backend.django import mixer

from posts.models import Group, Post, User


class TestPostModel(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = mixer.blend(User, username='RingoStarr')
        cls.group = mixer.blend(Group, slug='test-slug')
        mixer.blend(Post, author=cls.user)

    def test_models_have_correct_object_names(self):
        """Проверяем, что у модели Post корректно работает __str__."""
        post = Post.objects.first()
        expected_object_name = post.text[:15]
        self.assertEqual(expected_object_name, str(post))


class TestGroupModel(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.group = mixer.blend(Group, slug='test-slug')

    def test_models_have_correct_object_names(self):
        """Проверяем, что у модели Group корректно работает __str__."""
        group = Group.objects.first()
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))
