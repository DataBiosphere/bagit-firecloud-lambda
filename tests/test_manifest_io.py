#!/usr/bin/env python

import unittest
import os
from unittest import mock
from chalicelib.utils import ManifestIO, requests_response_to_chalice_Response

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

    @mock.patch.object(ManifestIO, 'workspace_exists')
    def test_workspace_exists(self, mock_get):

        mock_resp = self._mock_response()
        mock_get.return_value = mock_resp

        result = self.mani.workspace_exists()
        self.assertTrue(mock_get(), result)

    @mock.patch.object(ManifestIO, 'workspace_exists')
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
          "timestamp": 1,
          "causes": [],
          "stackTrace": [],
          "message": "Duplicated entities are not allowed in TSV: " 
                     "09df7aef-246a-57eb-9685-e1d4d18b55ab"
        }

        mock_resp = self._mock_response(status=400, json_data=args)
        mock_post.return_value = mock_resp

        result = self.mani._import_tsv_to_fc('participant')

        self.longMessage = True
        self.assertEqual(first=mock_post(), second=result)

    @mock.patch('chalicelib.utils.Retry')
    def test_retry(self, retry_mock):
        """Try urllib3 retry directly."""
        mock_response = self._mock_response(status=500)
        retry_mock.return_value = mock_response

        self.mani.workspace_url = 'http://httpbin.org/status/500'

        resp = self.mani.workspace_exists()
        self.assertEqual(retry_mock.return_value.status_code, resp.status_code)
        assert retry_mock.called

if __name__ == '__main__':
    unittest.main()