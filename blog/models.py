from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Tag")
    slug = models.SlugField(unique=True, blank=True)

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                related_name='posts', verbose_name="Auteur")
    title = models.CharField(max_length=300, verbose_name="Titre")
    slug = models.SlugField(unique=True, blank=True, max_length=350)
    excerpt = models.TextField(max_length=500, blank=True, verbose_name="Résumé")
    content = models.TextField(verbose_name="Contenu")
    cover_image = models.ImageField(upload_to='blog/', blank=True, null=True, verbose_name="Image de couverture")
    tags = models.ManyToManyField(Tag, blank=True, verbose_name="Tags")
    is_published = models.BooleanField(default=True, verbose_name="Publié")
    published_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de publication")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Article"
        verbose_name_plural = "Articles"
        ordering = ['-published_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog:post_detail', kwargs={'slug': self.slug})
