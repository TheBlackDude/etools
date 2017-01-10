import datetime
from unittest import skip

from EquiTrack.tests.mixins import FastTenantTestCase as TenantTestCase
from EquiTrack.factories import NotificationFactory

from post_office.models import EmailTemplate

from notification.models import Notification


class TestEmailNotification(TenantTestCase):

    def setUp(self):
        self.date = datetime.date.today()
        self.tenant.country_short_code = 'LEBA'
        self.tenant.save()

    def test_email_template_generation(self):

        notification = NotificationFactory()

        Notification.create_email_template(notification.template_name, "Test template", "Announcement from UNICEF.", "<h1>Announcement from UNICEF.</h1>")

        self.assertNotEqual(EmailTemplate.objects.count(), 0)
