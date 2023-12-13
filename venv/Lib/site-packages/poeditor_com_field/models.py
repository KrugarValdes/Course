# -*- coding: utf-8 -*-

from django.db import models


class Link(models.Model):
    term = models.TextField()
    count = models.IntegerField(default=0)
    exists_on_server = models.BooleanField(default=False)
    in_sync_with_server = models.BooleanField(default=False)
    references = models.TextField()

    def __unicode__(self):
        return (
            "Term(id={}, term={}, count={}, posted={}, references={})").format(
                self.pk, self.term, self.count, self.posted, self.references)
