import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from mixer.backend.django import mixer

from posts.constants import NUMBER_POST_PER_PAGE
from posts.forms import PostForm
from posts.models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TestViews(TestCase):
    '''Тестирование работы view-классов.'''

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = mixer.blend(User, username='RingoStarr')
        cls.group = mixer.blend(Group, slug='test-slug')
        mixer.cycle(NUMBER_POST_PER_PAGE + 3).blend(
            Post,
            author=cls.user,
            group=cls.group,
            text=mixer.sequence('Пост # {0}')
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.anon = Client()
        self.auth = Client()
        self.auth.force_login(mixer.blend(User, username='auth'))
        self.author = Client()
        self.author.force_login(TestViews.user)
        cache.clear()

    def test_first_page_contains_ten_records(self):
        '''Паджинатор: количество постов на первой странице равно 10.'''
        response = self.auth.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']),
                         NUMBER_POST_PER_PAGE)

    def test_second_page_contains_three_records(self):
        '''Паджинатор: количество постов на второй странице равно 3.'''
        response = self.auth.get(reverse('posts:index'), {'page': 2})
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_page_uses_correct_templates(self):
        '''Проверка на соответствие путей и шаблонов.'''
        pages_templates = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': 'RingoStarr'}):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': 1}):
                'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': 1}):
                'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for page, template in pages_templates.items():
            with self.subTest(page=page):
                response = self.author.get(page)
                self.assertTemplateUsed(response, template)

    def test_page_list_posts_correct_context(self):
        '''Проверка соответствия контекста списку постов.'''
        group = TestViews.group
        user = TestViews.user
        expected_context = {
            reverse('posts:index'):
                (Post.objects.select_related('author').
                    order_by('-pub_date')[:NUMBER_POST_PER_PAGE]),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}):
                group.posts.order_by('-pub_date')[:NUMBER_POST_PER_PAGE],
            reverse('posts:profile', kwargs={'username': user.username}):
                user.posts.order_by('-pub_date')[:NUMBER_POST_PER_PAGE]
        }
        for key, val in expected_context.items():
            with self.subTest(key=key, val=val):
                response = self.auth.get(key)
                self.assertEqual(
                    response.context['page_obj'][:NUMBER_POST_PER_PAGE],
                    list(val)
                )

    def test_page_post_detail_correct_context(self):
        '''Проверка соответствия контекста конкретного поста.'''
        user = TestViews.user
        expected_context = {
            'author':
                user,
            'count_posts':
                Post.objects.filter(author_id=user.id).count(),
            'post':
                Post.objects.get(id=1),
        }
        response = self.auth.get(
            reverse('posts:post_detail', kwargs={'post_id': 1})
        )
        for (key, val) in expected_context.items():
            with self.subTest(key=key, val=val):
                self.assertEqual(response.context[key], val)

    def test_page_edit_post_correct_form(self):
        '''Проверка контекста формы редактирования поста.'''
        expected_context = {
            'is_edit':
                True,
            'form':
                PostForm(instance=Post.objects.get(id=1)),
        }
        response = self.author.get(
            reverse('posts:post_edit', kwargs={'post_id': 1})
        )
        for (key, val) in expected_context.items():
            with self.subTest(key=key, val=val):
                self.assertEqual(str(response.context[key]), str(val))

    def test_page_create_post_correct_form(self):
        '''Проверка контекста формы создания поста.'''
        expected_context = {
            'is_edit': False,
            'form': PostForm(),
        }
        response = self.author.get(reverse('posts:post_create'))
        for (key, val) in expected_context.items():
            with self.subTest(key=key, val=val):
                self.assertEqual(str(response.context[key]), str(val))

    def test_pages_on_create_post_with_group(self):
        '''Проверка появления на страницах нового поста с указанием гуппы.'''
        group = TestViews.group
        user = TestViews.user
        old_context = {
            reverse('posts:index'):
                set((Post.objects.select_related('author').
                    order_by('-pub_date')[:NUMBER_POST_PER_PAGE])),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}):
                set(group.posts.order_by('-pub_date')[:NUMBER_POST_PER_PAGE]),
            reverse('posts:profile', kwargs={'username': user.username}):
                set(user.posts.order_by('-pub_date')[:NUMBER_POST_PER_PAGE])
        }
        Post.objects.create(
            author=user,
            group=group,
            text='Проверочный пост пользователя с указанием группы'
        )
        for key, val in old_context.items():
            with self.subTest(key=key, val=val):
                response = self.client.get(key)
                difference_set = set(
                    response.context['page_obj'][:NUMBER_POST_PER_PAGE]
                ).difference(val)
                self.assertEqual(len(difference_set), 1)

    def test_presence_image_in_context(self):
        '''Проверка передачи изображения в контексте.'''
        post = Post.objects.first()
        pages_names = (
            ('posts:index', None,),
            ('posts:group_list', (post.group.slug,)),
            ('posts:profile', (post.author.username,)),
        )
        for addres, param in pages_names:
            response = self.auth.get(reverse(addres, args=param))
            for post_page in response.context['page_obj'].object_list:
                if post_page.id == post.id:
                    break
            with self.subTest(post_page=post_page):
                self.assertIsNotNone(post_page.image)
        response = self.auth.get(
            reverse('posts:post_detail', args=(post.id,))
        )
        self.assertIsNotNone(response.context['post'].image)

    def test_comments_only_authorized(self):
        post = Post.objects.first()
        start_comment_set = set(post.comments.all())
        form_data = {'text': 'Тестовый текст'}
        address = reverse('posts:add_comment', args=(post.id,))
        self.anon.post(address, data=form_data, follow=True)
        finish_comment_set = set(
            post.comments.all()).difference(start_comment_set)
        self.assertEqual(len(finish_comment_set), 0)
        response = self.auth.post(address, data=form_data, follow=True)
        finish_comment_set = set(
            post.comments.all()).difference(start_comment_set)
        self.assertEqual(len(finish_comment_set), 1)
        self.assertEqual(
            list(finish_comment_set)[0].id,
            response.context['comments'][0].id
        )

    def test_caching_of_main_page(self):
        post = mixer.blend(Post, author=self.user, group=self.group)
        cache.clear()
        response = self.auth.get(reverse('posts:index'))
        post.delete()
        response_cached = self.auth.get(reverse('posts:index'))
        self.assertHTMLEqual(
            response.content.decode(), response_cached.content.decode())
        cache.clear()
        response_cleared_cache = self.auth.get(reverse('posts:index'))
        self.assertHTMLNotEqual(
            response.content.decode(), response_cleared_cache.content.decode())

    def test_following_for_auth_user(self):
        author_name = self.user.username
        start_set = set(
            self.auth.get(reverse('posts:follow_index')).context['page_obj']
        )
        self.auth.get(reverse('posts:profile_follow', args=(author_name,)))
        following_set = set(
            self.auth.get(reverse('posts:follow_index')).context['page_obj']
        )
        self.assertNotEqual(following_set, start_set)
        self.auth.get(reverse('posts:profile_unfollow', args=(author_name,)))
        unfollowing_set = set(        self.auth.get(reverse('posts:profile_follow', args=(author_name,)))

            self.auth.get(reverse('posts:follow_index')).context['page_obj']
        )
        self.assertEqual(unfollowing_set, start_set)

    def test_new_post_in_follows(self):
        auth_1 = Client()
        auth_1.force_login(mixer.blend(User, username='Followed'))
        self.auth_1.get(reverse('posts:profile_follow', args=(author_name,)))
        auth_2 = Client()
        auth_2.force_login(mixer.blend(User, username='UnFollowed'))
        