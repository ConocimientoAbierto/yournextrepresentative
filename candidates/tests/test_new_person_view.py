from urlparse import urlsplit

from mock import patch

from django_webtest import WebTest

from .auth import TestUserMixin
from .helpers import equal_call_args
from .fake_popit import (
    get_example_popit_json,
    FakeOrganizationCollection, FakePersonCollection
)

example_timestamp = '2014-09-29T10:11:59.216159'
example_version_id = '5aa6418325c1a0bb'

def fill_form(form, form_dict):
    for key, value in form_dict.items():
        form[key] = value

@patch('candidates.views.PopIt')
class TestNewPersonView(TestUserMixin, WebTest):

    @patch('candidates.views.NewPersonView.get_current_timestamp')
    @patch('candidates.views.NewPersonView.create_version_id')
    @patch('candidates.views.NewPersonView.create_person')
    def test_new_person_submission(
            self,
            mock_create_person,
            mock_create_version_id,
            mock_get_current_timestamp,
            mock_popit):
        # Get the constituency page:
        mock_popit.return_value.organizations = FakeOrganizationCollection
        mock_popit.return_value.persons = FakePersonCollection
        # Just a smoke test for the moment:
        response = self.app.get(
            '/constituency/65808/dulwich-and-west-norwood',
            user=self.user
        )
        mock_get_current_timestamp.return_value = example_timestamp
        mock_create_version_id.return_value = example_version_id
        # Get the add candidate form and fill in some values:
        form = response.forms['new-candidate-form']
        form_dict = {
            'name': 'Jane Doe',
            'party': 'Invented Party',
            'email': 'jane@example.com',
            'wikipedia_url': 'http://en.wikipedia.org/wiki/Jane_Doe',
        }
        fill_form(form, form_dict)
        submission_response = form.submit()
        # If there's no source specified, it shouldn't ever get to
        # update_person, and redirect back to the constituency page:
        self.assertEqual(0, mock_create_person.call_count)

        # Try again with the source field filled in:
        form['source'] = 'A test new person, source: http://example.org'
        submission_response = form.submit()

        expected_call_args = (
            {
                'date_of_birth': None,
                'email': u'jane@example.com',
                'homepage_url': u'',
                'name': u'Jane Doe',
                'party_memberships': {
                    '2015': {
                        'name': u'Invented Party'
                    }
                },
                'standing_in': {
                    '2015': {
                        'name': u'Dulwich and West Norwood',
                        'mapit_url': 'http://mapit.mysociety.org/area/65808'
                    }
                },
                'twitter_username': u'',
                'wikipedia_url': u'http://en.wikipedia.org/wiki/Jane_Doe',
            },
            {
                'information_source': u'A test new person, source: http://example.org',
                'ip': '127.0.0.1',
                'timestamp': example_timestamp,
                'username': u'john',
                'version_id': example_version_id,
            }
        )

        self.assertTrue(
            equal_call_args(
                expected_call_args,
                mock_create_person.call_args[0]
            ),
            "create_person was called with unpexected values"
        )

        split_location = urlsplit(submission_response.location)
        self.assertEqual(
            '/constituency/65808/dulwich-and-west-norwood',
            split_location.path
        )