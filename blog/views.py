from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Post, Tag


def post_list(request):
    posts = Post.objects.filter(is_published=True)
    tags = Tag.objects.all()
    tag_slug = request.GET.get('tag')
    search_query = request.GET.get('q', '')
    selected_tag = None

    if tag_slug:
        selected_tag = get_object_or_404(Tag, slug=tag_slug)
        posts = posts.filter(tags=selected_tag)

    if search_query:
        posts = posts.filter(
            Q(title__icontains=search_query) | Q(content__icontains=search_query)
        )

    return render(request, 'blog/list.html', {
        'posts': posts,
        'tags': tags,
        'selected_tag': selected_tag,
        'search_query': search_query,
    })


def post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug, is_published=True)
    related_posts = Post.objects.filter(is_published=True).exclude(pk=post.pk)[:3]
    return render(request, 'blog/detail.html', {
        'post': post,
        'related_posts': related_posts,
    })
