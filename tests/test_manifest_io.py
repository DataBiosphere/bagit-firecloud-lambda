#!/usr/bin/env python

import unittest
import os
from unittest import mock
from chalicelib.utils import ManifestIO, check_headers

base_path = os.path.abspath(os.path.dirname(__file__))


class TestManifestIO(unittest.TestCase):
    # Use fixtures.
    def setUp(self):
        data = {
            'participant': base_path + '/test_participant.tsv',
            'sample': base_path + '/test_sample.tsv'
        }
        url = 'https://api.firecloud.org/api/workspaces'
        workspace = 'test_workspace'
        namespace = 'test_namespace'
        self.mani = ManifestIO(data=data, url=url,
                               workspace=workspace, namespace=namespace)

    def tearDown(self):
        del self.mani

    def _mock_response(self,
                       status=200,
                       reason='OK',
                       json_data=None,
                       raise_for_status=None):
        """Helper function to build the response."""

        mock_resp = mock.Mock()
        # Mock raise_for_status call w/optional error.
        mock_resp.raise_for_status = mock.Mock()
        if raise_for_status:
            mock_resp.raise_for_status.side_effect = raise_for_status
        # Set status code and content.
        mock_resp.status_code = status
        mock_resp.reason = reason
        if json_data:
            mock_resp.json = mock.Mock(
                return_value=json_data
            )
        return mock_resp

    @mock.patch('requests.get')
    def test_workspace_exists(self, mock_get):

        mock_resp = self._mock_response()
        mock_get.return_value = mock_resp

        result = self.mani.workspace_exists()
        self.assertTrue(mock_get(), result)

    @mock.patch('requests.get')
    def test_workspace_does_not_exists(self, mock_get):

        msg = (str.join('/', (self.mani.namespace,
                              self.mani.workspace)) +
        'does not exist')
        args = {'causes': [],
                'message': msg,
                'source': 'rawls',
                'stackTrace': [],
                'statusCode': 404,
                'timestamp': 1523052919724}

        mock_resp = self._mock_response(status=404, json_data=args)
        # Set mock return response.
        mock_get.return_value = mock_resp

        result = self.mani.workspace_exists()
        self.assertTrue(mock_get(), result)

    @mock.patch('requests.post')
    def test_upload_entity(self, mock_post):
        """Test the response of the upload of the first TSV file, 
        participant, when it satisfies FC specifications."""

        # Response body.
        args = {"status": 200}

        mock_resp = self._mock_response(status=args['status'])
        mock_post.return_value = mock_resp

        result = self.mani._import_tsv_to_fc('participant')
        self.assertTrue(mock_post(), result)

    @mock.patch('requests.post')
    def test_upload_duplicate_entity(self, mock_post):

        # Put TSV files containing duplicate records into manifest object.
        self.mani.data = {
            'participant': base_path + '/test_participant_duplicate.tsv',
            'sample': base_path + '/test_sample_duplicate.tsv'
        }

        args = {
          "statusCode": 400,
          "source": "FireCloud",
          "timestamp": 1523378011717,
          "causes": [],
          "stackTrace": [],
          "message": "Duplicated entities are not allowed in TSV: 09df7aef-246a-57eb-9685-e1d4d18b55ab"
        }

        mock_resp = self._mock_response(status=400, json_data=args)
        mock_post.return_value = mock_resp

        result = self.mani._import_tsv_to_fc('participant')

        self.longMessage = True
        self.assertEqual(first=mock_post(), second=result, msg=args['message'])


def mocked_requests_get(url, headers):
    """Create a mock response object to replace `requests.get`."""
    class MockResponse:
        def __init__(self, headers, json_data, status_code):
            self.headers = headers
            self.json_data = json_data
            self.status_code = status_code
        # To mock JSON data in a response object we create a function.
        def json(self):
            return self.json_data

    return MockResponse(headers={"Content-Type": "application/json"},
                        json_data={"key1": "value1"},
                        status_code=201)

def mocked_requests_post(url, json, headers):
    """Mock a post requests such as in `_standup_workspace`."""
    class MockResponse:
        def __init__(self, headers, json_data, status_code):
            self.headers = headers
            self.json_data = json_data
            self.status_code = status_code
        # To mock JSON data in a response object we create a function.
        def json(self):
            return self.json_data

    return MockResponse(headers={"Content-Type": "application/json"},
                        json_data={"key1": "value1"},
                        status_code=201)

def mock_with_json(status_code):
    """Create a mock response object to replace `requests.get`
    that has a JSON object as an attribute. This is usually the case
    for 201 and 404 status codes."""
    class MockResponse:
        def __init__(self, headers, json_data, status_code):
            self.headers = headers
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    if status_code == 200: # workspace exists
        return MockResponse(headers={"Content-Type": "application/json"},
                            json_data={'key1': 'value1'},
                            status_code=200)
    elif status_code == 404: # does not exist
        return MockResponse(headers={"Content-Type": "application/json"},
                            json_data={'key1': 'value1'},
                            status_code=404)
def mock_with_text():
    """Create a mock response object to replace `requests.get`."""
    class MockResponse:
        def __init__(self, headers, text, status_code):
            self.headers = headers
            self.text = text
            self.status_code = status_code

    return MockResponse(headers={
        "Content-Type": "text/html; charset=iso-8859-1"},
                        text='some text',
                        status_code=401)



class TestUtils(unittest.TestCase):
    @mock.patch('chalicelib.utils.requests.get',
                side_effect=mocked_requests_get)
    def test_check_headers_with_json(self, mock_get):
        mani_args = {'data': None,
                     'url': 'https://api.firecloud.org/api/workspaces',
                     'workspace': 'test',
                     'namespace': 'firecloud-cgl',
                     'auth': None
                     }
        mani = ManifestIO(**mani_args)
        r = mani.workspace_exists()
        self.assertEqual(r.json(), {"key1": "value1"})

        body, headers = check_headers(r)
        self.assertEqual(body, {"key1": "value1"})
        self.assertEqual(headers, {"Content-Type": "application/json"})

    def test_check_headers_with_text(self):
        """Mocks a failed FC requests returning a 401."""
        response = mock_with_text()

        body, headers = check_headers(response)
        self.assertEqual(body, 'some text')
        self.assertEqual(headers,
                         {"Content-Type": "text/html; charset=iso-8859-1"})

    @mock.patch('chalicelib.utils.requests.post',
               side_effect=mocked_requests_post)
    def test_manage_workspace(self, mock_post):
        mani_args = {'data': None,
                     'url': 'https://api.firecloud.org/api/workspaces',
                     'workspace': 'test',
                     'namespace': 'firecloud-cgl',
                     'auth': None
                     }
        # Workspace exists.
        mani1 = ManifestIO(**mani_args)
        r1 = mock_with_json(200)
        mani1.manage_workspace(r1)
        self.assertEqual(mani1.status_codes['workspace_exists'],
                         r1.status_code)
        self.assertFalse(mani1.status_codes['stood_up_workspace'], False)

        # Workspace doesn't exist.
        mani2 = ManifestIO(**mani_args)
        r2 = mock_with_json(404)
        mani2.manage_workspace(r2)
        self.assertEqual(mani2.status_codes['workspace_exists'],
                         r2.status_code)
        # Create workspace successfully.
        mani3 = ManifestIO(**mani_args)
        r3 = mani3._standup_workspace()
        self.assertEqual(r3.json(), {"key1": "value1"})
        self.assertEqual(r3.status_code, 201)


if __name__ == '__main__':
    unittest.main()