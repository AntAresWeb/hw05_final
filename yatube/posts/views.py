from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.cache import cache_page

from posts.forms import CommentForm, PostForm
from posts.models import Follow, Group, Post, User
from posts.utils import get_page_of_list


@cache_page(20, key_prefix='index_page')
def index(request):
    '''Контроллер главной страницы.'''
    post_list = (Post.objects.select_related('author').
                 order_by('-pub_date'))
    context = {
        'page_obj': get_page_of_list(request, post_list),
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    '''Контроллер страницы группы.'''
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    context = {
        'group': group,
        'page_obj': get_page_of_list(request, post_list),
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    '''Контроллер страницы профиля автора (пользователя).'''
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.get(user=request.user, author=author)
    following = follow is not None
    post_list = author.posts.all()
    context = {
        'author': author,
        'following': following,
        'page_obj': get_page_of_list(request, post_list),
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    '''Контроллер страницы конкретного поста с id.'''
    post = get_object_or_404(Post, id=post_id)
    author = get_object_or_404(User, id=post.author_id)
    count_posts = Post.objects.filter(author_id=post.author_id).count()
    comments = post.comments.all()
    form = CommentForm(request.POST or None)
    context = {
        'author': author,
        'count_posts': count_posts,
        'post': post,
        'comments': comments,
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def add_comment(request, post_id):
    '''Контроллер добавления нового комментария к посту.'''
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id) 


@login_required
def post_create(request):
    '''Контроллер страницы нового поста.'''
    if request.method == 'POST':
        post = Post(author=request.user)
        form = PostForm(
            request.POST or None,
            files=request.FILES or None,
            instance=post
        )
        if form.is_valid():
            form.save()
            return redirect(reverse('posts:profile',
                            args=[request.user.username]))
    else:
        form = PostForm()

    context = {
        'is_edit': False,
        'form': form,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    '''Контроллер страницы редактирования поста.'''
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post_id)
    context = {'is_edit': True, }

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    context = {
        'is_edit': True,
        'form': form,
    }

    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect(f'/posts/{post_id}')
    else:
        return render(request, 'posts/create_post.html', context)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    context = {
        'page_obj': get_page_of_list(request, post_list),
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if not Follow.objects.filter(user=request.user, author=author).exists():
        Follow.objects.create(user=request.user, author=author)
    return redirect(reverse('posts:profile', args=[username]))


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.get(user=request.user, author=author)
    if follow is not None:
        follow.delete()
    return redirect(reverse('posts:profile', args=[username]))
