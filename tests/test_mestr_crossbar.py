from twisted.trial import unittest
from twisted.internet.defer import inlineCallbacks, Deferred, returnValue
from twisted.internet import reactor
import mock

from mestr import authenticate


class TestAppSession(unittest.TestCase):

    @inlineCallbacks
    def test_authenticate_with_no_dependencies(self):
        import json
        details = {}
        details['ticket'] = json.dumps({'application_name': 'test1',
                                        'version': 0.1})
        value = yield authenticate("realm1", "authid", details)
        self.assertEqual(value, "backend")

    @inlineCallbacks
    def test_authenticate_with_dependencies_launch_in_right_order(self):
        import json
        details = {}
        details['ticket'] = json.dumps({'application_name': 'test2',
                                        'version': 0.1})
        value = yield authenticate("realm1", "authid", details)

        self.assertEqual(value, "backend")

        details['ticket'] = json.dumps({'application_name': 'test3',
                                        'version': 0.2,
                                        'required_components': {'test2': 0.1}})
        value = yield authenticate("realm1", "authid", details)
        self.assertEqual(value, "backend")

    @inlineCallbacks
    def test_authenticate_with_dependencies_not_launch(self):
        import json
        details = {}

        details['ticket'] = json.dumps({'application_name': 'test5',
                                        'version': 0.,
                                        'required_components': {'NoMatch': 0.1}
                                        })
        value = authenticate("realm1", "authid", details)
        self.assertNoResult(value)
        details['ticket'] = json.dumps({'application_name': 'NoMatch',
                                        'version': 0.1})
        value = yield authenticate("realm1", "authid", details)
