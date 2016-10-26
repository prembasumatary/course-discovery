"""
This is a demonstration of the error reported at https://youtrack.jetbrains.com/issue/PY-7659. As far as I can tell,
capturing logging output seems to break PyCharm's parsing of Nose test output. Both of the tests below should fail.
Occasionally, they will appear as if they passed in PyCharm. The only output is similar to the line below:

##teamcity[testFailed details='Traceback (most recent call last):|n  File "/Library/Frameworks/Python.framework/Versions/3.5/lib/python3.5/unittest/case.py", line 58, in testPartExecutor|n    yield|n  File "/Library/Frameworks/Python.framework/Versions/3.5/lib/python3.5/unittest/case.py", line 600, in run|n    testMethod()|n  File "/Users/cblackburn/workspace/course-discovery/course_discovery/apps/core/tests/test_jetbrains.py", line 17, in test_with_logging|n    self.assertEqual(1, 2)|n  File "/Library/Frameworks/Python.framework/Versions/3.5/lib/python3.5/unittest/case.py", line 820, in assertEqual|n    assertion_func(first, second, msg=msg)|n  File "/Library/Frameworks/Python.framework/Versions/3.5/lib/python3.5/unittest/case.py", line 813, in _baseAssertEqual|n    raise self.failureException(msg)|nAssertionError: 1 != 2|n' message='Failure' name='test_with_logging ']

This project uses Python 3.5.
"""

import logging

from django.test import TestCase

logger = logging.getLogger(__name__)


class JetBrainsTests(TestCase):
    def test_with_logging(self):
        logger.warning('This is a test.')
        self.assertEqual(1, 2)

    def test_without_logging(self):
        self.assertEqual(1, 2)
