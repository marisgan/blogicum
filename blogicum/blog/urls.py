from django.urls import path  # type: ignore

from . import views

app_name = 'blog'

urlpatterns = [
    path('posts/<int:post_id>/',
         views.post_detail,
         name='post_detail'),
    path('posts/<int:post_id>/comment/',
         views.add_comment,
         name='add_comment'),
    path('posts/<int:post_id>/edit_comment/<int:comment_id>/',
         views.edit_comment,
         name='edit_comment'),
    path('posts/<int:post_id>/delete_comment/<int:comment_id>/',
         views.delete_comment,
         name='delete_comment'),
    path('posts/<int:post_id>/edit/',
         views.PostUpdateView.as_view(),
         name='edit_post'),
    path('posts/create/',
         views.PostCreateView.as_view(),
         name='create_post'),
    path('posts/<int:post_id>/delete/',
         views.PostDeleteView.as_view(),
         name='delete_post'),
    path('category/<slug:category_slug>/',
         views.category_posts,
         name='category_posts'),
    path('profile/<str:username>/',
         views.profile,
         name='profile'),
    path('profile/<str:username>/edit/',
         views.edit_profile,
         name='edit_profile'),
    path('', views.IndexListView.as_view(), name='index'),
]
