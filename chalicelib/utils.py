#!/usr/bin/env python

import requests
from chalice import Response


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
    :statusCode: (dict) dictionary holding the status codes of all HTTP
                 responses

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
        """Returns true if FireCloud workspace in the specified namespace
        exists, otherwise false.
        """
        url = self.workspace_url
        headers = dict(Accept='application/json',
                       Authorization=self.auth)
        return requests.get(url=url, headers=headers)

    def manage_workspace(self, response):
        """Go through cases of the response from `workspace_exists`, and
        take appropriate action."""
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
                body, headers = check_headers(r_create)
                return Response(
                    body=body,
                    headers=headers
                )
                # TODO: this could be due to another user having created a workspace
                # with that name, so ideally we should not abort here but loop back...
        else:
            # Workspace neither exists, nor does the response indicate that it
            # does not exist. Execution is aborted as some other reason is present,
            # such as workspace name is invalid / not present / not authorized
            # (401, 403) or backend is having issues (5xx) such as possibly
            # an illegal workspace name (probably some 4xx).
            body, headers = check_headers(response)
            return Response(
                body=body,
                headers=headers
            )

    def upload_files(self, tsv_file_list):
        for filename in tsv_file_list:
            r_import = self._import_tsv_to_fc(filename)
            if r_import.status_code == 200:
                self.status_codes[filename + '_upload'] = r_import.status_code
                self.status_codes['workspace_url'] = r_import.url
            else:
                body, headers = check_headers(r_import)
                return Response(
                    body=body,
                    headers=headers
                )

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


# Standalone utility functions.

def check_headers(response):
    """Check if HTTP response header contains the `Content-Type` attribute."""
    if 'Content-Type' in response.headers.keys():
        body = get_content_type(response)
        headers = {'Content-Type': response.headers['Content-Type']}
    else:
        body = response.text  # worst case it's an empty string
        headers = {}
    return body, headers

def get_content_type(response):
    """The FC HTTP response can contain different content types. If the content
    type is `application/json` it returns this, otherwise return as text."""
    if 'json' in response.headers['Content-Type']:
        return response.json()
    else:
        return response.text


