#!/usr/bin/env python

import requests


class ManifestIO:
    """
    Handles manifest downloaded from a metadata portal
    by the user. Has methods that check for workspace existence,
    creates a new workspace, and uploads two files pointed to in
    the payload into a namespace on Broad's FireCloud analysis platform.

    :payload: (list) of strings representing paths to
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

    def __init__(self, data,
                 url=None, workspace=None, namespace=None, auth=None):
        self.data = data
        if url is not None:
            self.url = url + '/' + namespace + '/' + workspace
        self.workspace = workspace
        self.namespace = namespace
        self.auth = auth  # private

    def workspace_exists(self):
        """Returns true if FireCloud workspace in the specified namespace
        exists, otherwise false.
        """
        headers = dict(Accept='application/json',
                       Authorization=self.auth)
        r = requests.get(self.url, headers=headers)
        if r.status_code == 200:
            return True
        else:
            return False

    def standup_workspace(self):
        """
        Creates workspace in specified namespace.
        """
        url = self._prune_url()
        payload = self._make_payload()
        headers = {
            'Authorization': self.auth,
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        # (note: only works with calling "json" as the data parameter)
        r = requests.post(url, json=payload, headers=headers)
        if r.status_code == 201:
            print("created workspace")
        elif r.status_code == 409:
            print("workspace already exists")
        elif r.status_code == 405:
            print("likely malformed URL")
        elif r.status_code == 401:
            print("not authorized")
        else:
            print("not sure what's happening")

    def import_tsv_to_fc(self):
        """
        Uploads "participant", a Pandas Series (which needs
        to be uploaded first), and a dataframe "sample" (which
        needs to be uploaded after "participant") to the FC
        workspace.
        """
        # Check whether the workspace exists in this namespace,
        # otherwise create it.
        if not self.workspace_exists():
            self.standup_workspace()

        # Create FC endpoint for TSV file upload.
        _url = '/importEntities'
        url = self.url + _url

        # Header for both request calls.
        headers = {
            'Authorization': self.auth,
            'Accept': 'application/json'
        }

        # Upload "participant.
        with open(self.data[0], 'rb') as f:
            files = {'entities': f}
            r1 = requests.post(url, files=files, headers=headers)

        # Upload "sample".
        with open(self.data[1], 'rb') as f:
            files = {'entities': f}
            r2 = requests.post(url, files=files, headers=headers)

        return {"participant": r1.status_code,
                "sample": r2.status_code}

    def _make_payload(self):
        payload = dict(zip(
            ['attributes',
             'authorizationDomain',
             'name',
             'namespace'],
            [{},
             [],
             self.workspace,
             self.namespace]))
        return payload

    def _prune_url(self):
        """Returns URL without workspace and namespace."""
        sep = '/'
        url = self.url.rsplit(sep, 2)[0]
        return url
