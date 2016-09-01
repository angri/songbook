from django.db import models
from django.contrib.auth.models import User


class CommentManager(models.Manager):
    def get_queryset(self):
        qs = super(CommentManager, self).get_queryset()
        return qs.select_related('song', 'author', 'gig')


class Comment(models.Model):
    objects = CommentManager()

    CT_SONG_COMMENT = 'song_comment'
    CT_SONG_EDIT = 'song_changed'
    CT_GIG_COMMENT = 'gig_comment'
    CT_GIG_EDIT = 'gig_changed'

    COMMENT_TYPE_CHOICES = (
        (CT_SONG_COMMENT, CT_SONG_COMMENT),
        (CT_GIG_COMMENT, CT_GIG_COMMENT),
        (CT_SONG_EDIT, CT_SONG_EDIT),
    )
    GIG_ONLY_COMMENTS = (CT_GIG_COMMENT, CT_GIG_EDIT)

    gig = models.ForeignKey('sbgig.Gig', on_delete=models.CASCADE,
                            blank=False, related_name='comments')
    song = models.ForeignKey('sbsong.Song', on_delete=models.CASCADE,
                             blank=True, null=True, related_name='comments')
    comment_type = models.CharField(max_length=20, null=False, blank=False,
                                    choices=COMMENT_TYPE_CHOICES)
    author = models.ForeignKey(User, on_delete=models.PROTECT,
                               null=True, blank=True,
                               related_name='comments')
    datetime = models.DateTimeField(auto_now_add=True)
    text = models.TextField(null=False, blank=False)

    class Meta:
        ordering = ['-datetime']
        index_together = [
            ['author', 'datetime'],
            ['gig', 'datetime'],
            ['song', 'datetime'],
        ]
