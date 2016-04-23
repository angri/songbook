from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _


class Gig(models.Model):
    title = models.CharField(verbose_name=_("Gig name"),
                             max_length=60, blank=False)
    slug = models.SlugField(verbose_name=_("Slug"), blank=False)
    date = models.DateField(verbose_name=_("Gig date"), blank=False)
    description = models.TextField(verbose_name=_("Description"),
                                   null=False, blank=True)

    def __str__(self):
        return "%s (%s)" % (self.title, self.date)


class CommentManager(models.Manager):
    def get_queryset(self):
        qs = super(CommentManager, self).get_queryset()
        return qs.select_related('song', 'author', 'gig')


class Comment(models.Model):
    objects = CommentManager()

    CT_SONG_COMMENT = 'song_comment'
    CT_SONG_EDIT = 'song_changed'
    CT_GIG_COMMENT = 'gig_comment'

    COMMENT_TYPE_CHOICES = (
        (CT_SONG_COMMENT, CT_SONG_COMMENT),
        (CT_GIG_COMMENT, CT_GIG_COMMENT),
        (CT_SONG_EDIT, CT_SONG_EDIT),
    )
    gig = models.ForeignKey(Gig, on_delete=models.CASCADE,
                            blank=False, related_name='comments')
    song = models.ForeignKey('sb.Song', on_delete=models.CASCADE,
                             blank=True, null=True, related_name='comments')
    comment_type = models.CharField(max_length=20, null=False, blank=False,
                                    choices=COMMENT_TYPE_CHOICES)
    author = models.ForeignKey(User, on_delete=models.PROTECT,
                               null=True, blank=True,
                               related_name='comments')
    datetime = models.DateTimeField(auto_now_add=True)
    text = models.TextField(null=False, blank=False)

    class Meta:
        ordering = ['gig', 'song', '-datetime']
        index_together = [
            ['author', 'datetime'],
            ['gig', 'song', 'comment_type', 'datetime']
        ]
