#!/usr/bin/env python

import requests
from urllib3 import Retry
from requests.adapters import HTTPAdapter
from requests import Session
from chalicelib.utils import requests_response_to_chalice_Response


class ManifestIO:
    """
    Handles manifest downloaded from a metadata portal
    by the user. Has methods that check for workspace existence,
    creates a new workspace, and uploads two files pointed to in
    the payload into a namespace on Broad's FireCloud analysis platform.

    :data: (list) of strings representing paths to
            participant (element [0])
            and sample (element [1])
    :url: (str) base url for FireCloud (FC) workspaces
    :workspace: (str) FC workspace (does not need to exist)
    :namespace: (str) FC namespace
    :auth: (str) filename of bearer token to authenticate to FC

    TODO: - check whether list has two elements
          - check which of those elements contains the participant,
            and which the sample, such that we do not need to hardcode
            it
          - programmatically check identity and validity of files
            pointed to in payload (independent of naming)
          - avoid writing to TSVs to disk altogether
    """

    def __init__(self, data, url, workspace, namespace, auth=None):
        self.data = data
        self.base_url = url
        self.workspace_url = url + '/' + namespace + '/' + workspace
        self.workspace = workspace
        self.namespace = namespace
        self.auth = auth
        # Dict to collect status codes (or booleans) for successful operations.
        self.status_codes = {
            'workspace_exists': '',
            'stood_up_workspace': ''
        }

    def workspace_exists(self):
        """Returns requests response object. Status code is 200 if FireCloud 
        workspace in the specified workspace exists, or 404 if it doesn't."""
        url = self.workspace_url
        headers = dict(Accept='application/json',
                       Authorization=self.auth)
        # Start a session with 3 GET retries.
        s = Session()

        # The reason for the 401 in status_forcelist is because we
        # have seen it occurring in FC requests.
        s.mount('https://', HTTPAdapter(
            max_retries=Retry(total=4,
                              backoff_factor=1,
                              raise_on_status=False,
                              status_forcelist=[401, 500, 502, 503, 504])
        ))
        resp = s.get(url=url, headers=headers)

        return resp

    def manage_workspace(self, response):
        """Go through cases of the response from `workspace_exists`, and
        take appropriate action.

        :response: a request response object
        """
        if response.status_code == 200:
            # Workspace exists.
            self.status_codes['workspace_exists'] = response.status_code
            self.status_codes['stood_up_workspace'] = False
        elif response.status_code == 404:
            # ...does not exist
            self.status_codes['workspace_exists'] = response.status_code
            r_create = self._standup_workspace()
            if r_create.status_code == 201:
                self.status_codes['stood_up_workspace'] = \
                    r_create.status_code
            else:  # something went wrong when creating workspace
                return requests_response_to_chalice_Response(r_create)

                # TODO: this could be due to another user having created a workspace
                # with that name, so ideally we should not abort here but loop back...
        else:
            # Workspace neither exists, nor does the response indicate that it
            # does not exist. Execution is aborted as some other reason is present,
            # such as workspace name is invalid / not present / not authorized
            # (401, 403) or backend is having issues (5xx) such as possibly
            # an illegal workspace name (probably some 4xx).
            return requests_response_to_chalice_Response(response)

    def upload_files(self, tsv_file_list):
        for filename in tsv_file_list:
            r_import = self._import_tsv_to_fc(filename)
            if r_import.status_code == 200:
                self.status_codes[filename + '_upload'] = r_import.status_code
                self.status_codes['workspace_url'] = r_import.url
            else:
                return requests_response_to_chalice_Response(r_import)

    def _standup_workspace(self):
        """
        Creates workspace in specified namespace.
        """
        url = self.base_url
        payload = self._make_payload()
        headers = {
            'Authorization': self.auth,
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        # (note: only works with calling "json" as the data parameter)
        return requests.post(url=url, json=payload, headers=headers)

    def _import_tsv_to_fc(self, tsv_file_name):
        """
        Uploads two TSV files "participant" and "sample" (which needs to
        be uploaded after "participant") to the FC workspace.
        """
        # FC endpoint for TSV file upload.
        url = self.workspace_url + '/importEntities'

        # Header for both request calls.
        headers = {
            'Authorization': self.auth,
            'Accept': 'application/json'
        }

        with open(self.data[tsv_file_name], 'rb') as f:
            files = {'entities': f}
            response = requests.post(url=url, files=files, headers=headers)

            return response

    def _make_payload(self):
        payload = {
            'attributes': {},
            'authorizationDomain': [],
            'name': self.workspace,
            'namespace': self.namespace
        }
        return payload
