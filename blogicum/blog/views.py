from datetime import datetime

from django.contrib.auth.mixins import (  # type: ignore
    LoginRequiredMixin, UserPassesTestMixin
)
from django.contrib.auth.decorators import login_required  # type: ignore
from django.core.exceptions import PermissionDenied  # type: ignore
from django.core.paginator import Paginator  # type: ignore
from django.http import Http404  # type: ignore
from django.http.response import HttpResponseRedirect  # type: ignore
from django.shortcuts import (  # type: ignore
    get_object_or_404, redirect, render
)
from django.urls import reverse  # type: ignore
from django.views.generic import (  # type: ignore
    CreateView, DetailView, DeleteView, ListView, UpdateView
)

from .forms import CommentForm, PostForm, ProfileForm
from .models import Comment, Post, Category, User

POSTS_PER_PAGE = 10


def paginate_posts(request, posts):
    return Paginator(posts, POSTS_PER_PAGE).get_page(request.GET.get('page'))


def filter_published(posts):
    return posts.select_related(
        'author', 'category', 'location'
    ).filter(
        pub_date__date__lte=datetime.now(),
        is_published=True,
        category__is_published=True,
    )


class OnlyAuthorMixin(UserPassesTestMixin):

    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user


def profile(request, username):
    profile = get_object_or_404(User, username=username)
    if request.user.is_authenticated and request.user == profile:
        posts = profile.posts.select_related('author', 'category', 'location')
    else:
        posts = filter_published(profile.posts)
    return render(request, 'blog/profile.html', {
        'profile': profile,
        'page_obj': paginate_posts(request, posts),
    })


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True)
    return render(request, 'blog/category.html', {
        'category': category,
        'page_obj': paginate_posts(request, filter_published(category.posts)),
    })


@login_required
def edit_profile(request, username):
    instance = get_object_or_404(User, username=username)
    if instance != request.user:
        raise PermissionDenied
    form = ProfileForm(request.POST or None, instance=instance)
    if form.is_valid():
        form.save()
    return render(request, 'blog/user.html', {'form': form})


class IndexListView(ListView):
    model = Post
    queryset = filter_published(Post.objects)
    template_name = 'blog/index.html'
    paginate_by = POSTS_PER_PAGE


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        self.object = get_object_or_404(Post, id=kwargs['post_id'])
        if self.object.author != request.user and not self.object.is_published:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = (
            self.object.comments.select_related('author')
        )
        return context


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


class PostUpdateView(OnlyAuthorMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        self.object = get_object_or_404(Post, pk=kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def handle_no_permission(self):
        return HttpResponseRedirect(
            reverse('blog:post_detail', kwargs={'post_id': self.object.pk})
        )

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self.object.id})


class PostDeleteView(OnlyAuthorMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(
        filter_published(Post.objects),
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
        raise PermissionDenied()
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
        raise PermissionDenied()
    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id=post_id)
    return render(request, 'blog/comment.html', {'comment': comment})
