import ddt
from django.core.urlresolvers import reverse
from django.test import TestCase

from course_discovery.apps.core.tests.factories import UserFactory
from course_discovery.apps.publisher.models import CourseRun
from course_discovery.apps.publisher.tests import factories


USER_PASSWORD = 'password'


# pylint: disable=no-member
@ddt.ddt
class AdminTests(TestCase):
    """ Tests Admin page."""

    def setUp(self):
        super(AdminTests, self).setUp()
        self.user = UserFactory(is_staff=True, is_superuser=True)
        self.client.login(username=self.user.username, password=USER_PASSWORD)
        self.course_run = factories.CourseRunFactory(lms_course_id='', changed_by=self.user)
        self.change_url = reverse('admin:publisher_courserun_add')
        self.form = self.client.get(self.change_url)

        self.assertFalse(CourseRun.objects.filter(lms_course_id__isnull=True).exists())

    def test_update_course_form(self):
        """ Verify that admin save the none in case of empty lms-course-id."""

        # in case of empty string no data appears.
        data = self._post_data(self.course_run)
        self.client.post(self.change_url, data=data)
        self.assertTrue(CourseRun.objects.filter(lms_course_id__isnull=True).exists())

    def _post_data(self, course_run):
        return {
            'lms_course_id': '',
            'pacing_type': course_run.pacing_type,
            'course': course_run.course.id,
            'start_0': course_run.start.date(),
            'start_1': course_run.start.time(),
            'end_0': course_run.end.date(),
            'end_1': course_run.end.time(),
            'state': course_run.state.id,
            'contacted_partner_manager': course_run.contacted_partner_manager,
            'changed_by': course_run.changed_by.id
        }

    def test_user_attributes_admin(self):
        """ Verify that user attribute admin form loads detail page successfully."""
        user_attr = factories.UserAttributeFactory()
        change_url = reverse('admin:publisher_userattributes_change', args=(user_attr.id,))
        self._assert_response(change_url)

    def _assert_response(self, url):
        """ Verify page loads successfully."""
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
