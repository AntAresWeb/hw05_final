from django import forms

from posts.models import Comment, Post


class PostForm(forms.ModelForm):
    '''Форма для поста (сообщения).'''
    class Meta:
        model = Post
        fields = ['text', 'group', 'image']


class CommentForm(forms.ModelForm):
    '''Форма для комментария к сообщению.'''
    class Meta:
        model = Comment
        fields = ['text']