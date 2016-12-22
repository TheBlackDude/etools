from __future__ import absolute_import

import datetime
from dateutil.relativedelta import relativedelta

from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField, ArrayField
from django.db import models, connection, transaction
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from model_utils import Choices


class Notification(models.Model):
    """
    Represents a notification instance from sender to recipients

    Relates to :model:`django.contrib.auth.models.User`
    """

    TYPE_CHOICES = Choices(
        ('Email', 'Email'),
    )

    type = models.CharField(max_length=255, choices=TYPE_CHOICES)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    sender = GenericForeignKey('content_type', 'object_id')
    recipients = models.ForeignKey(User, related_name="notifications")
    template_name = models.CharField(max_length=255)
    template_data = JSONField()

    def __unicode__(self):
        return "{} Notification from {}: {}".format(self.type, self.sender, self.template_data)
