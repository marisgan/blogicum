from datetime import datetime

from django.contrib.auth.mixins import (  # type: ignore
    LoginRequiredMixin, UserPassesTestMixin
)
from django.contrib.auth.decorators import login_required  # type: ignore
from django.core.paginator import Paginator  # type: ignore
from django.db.models import Count  # type: ignore
from django.shortcuts import (  # type: ignore
    get_object_or_404, redirect, render
)
from django.urls import reverse  # type: ignore
from django.views.generic import (  # type: ignore
    CreateView, DeleteView, ListView, UpdateView
)

from .forms import CommentForm, PostForm, ProfileForm
from .models import Comment, Post, Category, User

POSTS_PER_PAGE = 10


def paginate_posts(request, posts):
    return Paginator(posts, POSTS_PER_PAGE).get_page(request.GET.get('page'))


def make_feed(posts, filtrate=True):
    feed = posts.select_related(
        'author', 'category', 'location'
    ).annotate(
        comments_count=Count('comments')
    ).order_by(*Post._meta.ordering)
    if filtrate:
        return feed.filter(
            pub_date__date__lte=datetime.now(),
            is_published=True,
            category__is_published=True,
        )
    return feed


def profile(request, username):
    author = get_object_or_404(User, username=username)
    return render(request, 'blog/profile.html', {
        'profile': author,
        'page_obj': paginate_posts(request, make_feed(
            author.posts, request.user != author))
    })


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True)
    return render(request, 'blog/category.html', {
        'category': category,
        'page_obj': paginate_posts(
            request, make_feed(category.posts)),
    })


@login_required
def edit_profile(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        return redirect('blog:profile', username=username)
    form = ProfileForm(request.POST or None, instance=author)
    if form.is_valid():
        form.save()
        return redirect('blog:profile', username=username)
    return render(request, 'blog/user.html', {'form': form})


class IndexListView(ListView):
    model = Post
    queryset = make_feed(Post.objects)
    template_name = 'blog/index.html'
    paginate_by = POSTS_PER_PAGE


def post_detail(request, post_id):
    post = get_object_or_404(
        make_feed(Post.objects, filtrate=False),
        id=post_id)
    if request.user != post.author:
        post = get_object_or_404(
            make_feed(Post.objects, filtrate=True),
            id=post_id)
    return render(request, 'blog/detail.html', {
        'post': post,
        'form': CommentForm(),
        'comments': post.comments.select_related('author'),
    })


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class OnlyAuthorMixin(UserPassesTestMixin):

    def test_func(self):
        return self.get_object().author == self.request.user


class PostUpdateView(OnlyAuthorMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def handle_no_permission(self):
        return redirect(reverse(
            'blog:post_detail',
            kwargs={'post_id': self.get_object().id}
        ))


class PostDeleteView(OnlyAuthorMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def get_success_url(self):
        return reverse(
            'blog:profile',
            args=[self.request.user.username]
        )


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(
        make_feed(Post.objects),
        pk=post_id
    )
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('blog:post_detail', post_id=post_id)


@login_required
def edit_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)
    form = CommentForm(request.POST or None, instance=comment)
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id=post_id)
    return render(request, 'blog/comment.html', {
        'comment': comment,
        'form': form
    })


@login_required
def delete_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    if comment.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)
    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id=post_id)
    return render(request, 'blog/comment.html', {'comment': comment})
