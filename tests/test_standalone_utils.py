#!/usr/bin/env python

import unittest
from unittest import mock
from chalicelib.utils import ManifestIO, check_headers, \
    requests_response_to_chalice_Response
from collections import Mapping


def mocked_requests_get():
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
    """Create a mock requests response object to replace `requests.get`."""
    class MockResponse:
        def __init__(self, headers, text, status_code):
            self.headers = headers
            self.text = text
            self.status_code = status_code

    return MockResponse(
        headers={"Content-Type": "text/html; charset=iso-8859-1"},
        text='some text',
        status_code=401)

class TestUtils(unittest.TestCase):
    @mock.patch.object(ManifestIO, 'workspace_exists',
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


    def test_requests_response_to_chalice_Response(self):

        # Mock a requests response object.
        class MockRequestsResponse():
            def __init__(self, text, headers, statusCode):
                self.text = text
                self.headers = MyDict(headers)
                self.status_code = statusCode

        text = ('<head>\n<title>Error response</title>\n</head>\n<body>\n'
                '<h1>Error response</h1>\n<p>Error code 404.\n'
                '<p>Message: File not found.\n<p>'
                'Error code explanation: 404 = '
                'Nothing matches the given URI.\n</body>\n')

        headers = {'Server': 'SimpleHTTP/0.6 Python/2.7.12',
                   'Date': 'Wed, 25 Apr 2018 18:41:38 GMT',
                   'Connection': 'close',
                   'Content-Type': 'text/html'}

        # We need this class to mock the `KeysView` of the headers dictionary,
        # which is a feature or the response object.
        class MyDict(Mapping):
            def __init__(self, dct):
                self._dct = dct

            def __getitem__(self, key):
                return self._dct[key]

            def __iter__(self):
                return iter(self._dct)

            def __len__(self):
                return len(self._dct)

            def __repr__(self):
                return '{self.__class__.__name__}({self._dct})'.format(
                    self=self)

        mock_resp = MockRequestsResponse(text=text, headers=headers,
                                        statusCode=200)

        resp = requests_response_to_chalice_Response(mock_resp)

        assert(resp.status_code == mock_resp.status_code)
        assert(resp.headers == {'Content-Type': 'text/html'})
        assert(resp.body == mock_resp.text)


        json_data = {'accessLevel': 'OWNER',
                     'canCompute': True,
                     'canShare': True,
                     'name': 'test16',
                     'namespace': 'firecloud-cgl',
                     'workspaceId': '8181bcc2-89e3-42be-9a67-7a6681b74695'
                     }

        headers = {'Server': 'SimpleHTTP/0.6 Python/2.7.12',
                   'Date': 'Wed, 25 Apr 2018 18:41:38 GMT',
                   'Connection': 'close',
                   'Content-Type': 'application/json'}

        class MockRequestsResponse():
            def __init__(self, json_data, headers, statusCode):
                self.json_data = json_data
                self.headers = MyDict(headers)
                self.status_code = statusCode

            def json(self):
                return self.json_data

        mock_resp = MockRequestsResponse(json_data=json_data, headers=headers,
                                         statusCode=200)

        assert('Content-Type' in mock_resp.headers.keys())
        resp = requests_response_to_chalice_Response(mock_resp)

        self.assertEqual(resp.body, mock_resp.json_data)
        self.assertEqual(resp.headers, {'Content-Type': 'application/json'})
        self.assertEqual(resp.status_code, mock_resp.status_code)


if __name__ == '__main__':
    unittest.main()