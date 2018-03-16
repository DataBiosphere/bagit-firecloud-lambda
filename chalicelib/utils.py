#!/usr/bin/env python

import requests
import io
import pandas as pd


class ManifestIO:
    """
    Handles a metadata manifest downloaded from a data portal
    by the user, creates a workspace in a namespace on Broad's
    FireCloud analysis platform.

    :payload: (list) of BytesIO file-objects of
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
        Create workspace in specified namespace.
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
        Returns a tuple containing the a "participant" dataframe
        (which needs to be uploaded first), and a dataframe "df",
        which is technically is the "sample" dataset, and which
        needs to be uploaded after the participant, to be
        in FireCloud-compliant format to be uploaded.

        :param url: (str)
        :param payload: (dict)
        :param tsv_fname: (str)
        :param auth: (str)
        :param df: (Pandas dataframe)
        :return: response objects
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

        # Upload "participant (as Pandas Series).
        participant = pd.read_csv(self.data[0], sep='\t', squeeze=True)
        participant_buf = io.StringIO()
        participant.to_csv(
            path=participant_buf,
            sep='\t',
            index=False,
            header=True
        )
        participant_buf.seek(0)
        files = {'entities': participant_buf}
        r1 = requests.post(url, files=files, headers=headers)

        # Upload "sample".
        sample = pd.read_csv(self.data[1], sep='\t')
        sample_buf = io.StringIO()
        sample.to_csv(
            path_or_buf=sample_buf,
            sep='\t',
            index=False,
            header=True
        )
        sample_buf.seek(0)
        files = {'entities': sample_buf}
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
