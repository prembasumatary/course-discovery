import ddt
import mock
import pytest
from django.conf import settings
from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings
from elasticsearch import Elasticsearch
from freezegun import freeze_time

from course_discovery.apps.core.tests.mixins import ElasticsearchTestMixin
from course_discovery.apps.course_metadata.tests.factories import CourseRunFactory
from course_discovery.apps.edx_haystack_extensions.tests.mixins import SearchIndexTestMixin

@ddt
@override_settings(HAYSTACK_SIGNAL_PROCESSOR='haystack.signals.BaseSignalProcessor')
class UpdateIndexTests(ElasticsearchTestMixin, SearchIndexTestMixin, TestCase):
    @freeze_time('2016-06-21')
    def test_handle(self):
        """ Verify the command creates a timestamped index and repoints the alias. """
        with mock.patch('course_discovery.apps.edx_haystack_extensions.management.commands.'
                        'update_index.Command.sanity_check_new_index', return_value=(True, '')):
            call_command('update_index')

        alias = settings.HAYSTACK_CONNECTIONS['default']['INDEX_NAME']
        index = '{alias}_20160621_000000'.format(alias=alias)

        host = settings.HAYSTACK_CONNECTIONS['default']['URL']
        connection = Elasticsearch(host)
        response = connection.indices.get_alias(name=alias)
        expected = {
            index: {
                'aliases': {
                    alias: {}
                }
            }
        }
        self.assertDictEqual(response, expected)

    @ddt.data(False, True)
    def test_sanity_check_error(self, sanity_check_disabled):
        """ Verify the command raises a CommandError if new index fails the sanity check.
        But does not raise an error if the sanity check is disabled. """
        CourseRunFactory()
        record_count = 2
        additional_runs = int(100 * settings.INDEX_SIZE_CHANGE_THRESHOLD + 1)
        CourseRunFactory.create_batch(additional_runs)

        # Ensure that an error is raised if the sanity check does not pass
        with pytest.raises(CommandError):
            with mock.patch('course_discovery.apps.edx_haystack_extensions.management.commands.'
                            'update_index.Command.set_alias', return_value=True):
                with mock.patch('course_discovery.apps.edx_haystack_extensions.management.commands.'
                                'update_index.Command.get_record_count', return_value=record_count):
                    command_args = ['--sanity-check-disabled'] if sanity_check_disabled else []
                    call_command('update_index', *command_args)


    def test_sanity_check_success(self):
        """ Verify the command does not raise a CommandError error if the new index passes the sanity check. """
        CourseRunFactory.create_batch(30)
        record_count = 60
        additional_runs = int(10 * settings.INDEX_SIZE_CHANGE_THRESHOLD - 1)
        CourseRunFactory.create_batch(additional_runs)

        # Ensure that no error is raised and the sanity check passes the second time
        with mock.patch('course_discovery.apps.edx_haystack_extensions.management.commands.'
                        'update_index.Command.set_alias', return_value=True):
            with mock.patch('course_discovery.apps.edx_haystack_extensions.management.commands.'
                            'update_index.Command.get_record_count', return_value=record_count):
                call_command('update_index')
