#!/usr/bin/env python

import requests
import pandas as pd
import io


class ManifestIO:
    """
    Handles a metadata manifest from Boardwalk, created by the
    user, reformats it, creates a workspace in a namespace of
    of Broad's FireCloud analysis platform.

    :flo: (str) a binary file-like object of the TSV metadata file
    :url: (str) base url for FireCloud (FC) workspaces
    :workspace: (str) FC workspace (does not need to exist)
    :namespace: (str) FC namespace
    :auth: (str) filename of bearer token to authenticate to FC
    """

    def __init__(self, flo,
                 url=None, workspace=None, namespace=None, auth=None):
        self.df = pd.read_csv(flo, sep='\t')  # create Pandas dataframe
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

        # Transform the dataframe to make it compatible with FireCloud.
        participant, sample = self._transform_df()
        _url = '/importEntities'
        url = self.url + _url
        # Header for both request calls.
        headers = {
            'Authorization': self.auth,
            'Accept': 'application/json'
        }
        # Create file-like object (stream) from the Pandas dataframe.
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

    def _transform_df(self):
        """Transforms dataframe df for FireCloud upload and returns
        two dataframes, a tuple of participant and sample, which are then
        uploaded to FireCloud in that order.
        """
        df = self.df
        # Remove all spaces from column headers and make lower case.
        df.rename(columns=lambda x: x.replace(" ", "_"), inplace=True)
        df.rename(columns=lambda x: x.lower(), inplace=True)
        # Start normalizing the table. First, slice by file type.
        df1 = df[df['file_type'] == 'crai']
        df2 = df[['file_type',
                  'file_path',
                  'upload_file_id']][df['file_type'] == 'cram']
        df2.rename(index=str,
                   columns={'file_type': 'file_type2',
                            'file_path': 'file_path2',
                            'upload_file_id': 'upload_file_id2'},
                   inplace=True)
        frames = [df1, df2]  # merge both frames
        for frame in frames:
            frame.reset_index(drop=True, inplace=True)
        # Second, by combining df1 and df2 we obtain a normalized table,
        # using the index from df1.
        df_new = pd.concat(frames, axis=1, join_axes=[df1.index])
        df_new.drop_duplicates(keep='first', inplace=True)
        # Create a table with only one column (donor will be participant
        # in FC).
        participant = df_new['donor_uuid']  # extract one column
        participant.name = 'entity:participant_id'  # rename column header

        # Re-order index of dataframe to be compliant with FireCloud
        # specifications.
        new_index = ([11, 4, 3, 7, 5, 6, 8, 9, 10, 12, 13, 14] +
                     [0, 1, 2, 18, 19, 15, 16, 17, 20, 21, 22])
        L = df_new.columns.tolist()
        new_col_order = [L[x] for x in new_index]
        df_new = df_new.reindex(columns=new_col_order)
        sample = df_new.rename(
            index=str,
            columns={'sample_uuid': 'entity:sample_id',
                     'donor_uuid': 'participant_id',
                     'file_type': 'file_type1',
                     'file_path': 'file_path1',
                     'upload_file_id': 'upload_file_id1',
                     'metadata.json': 'metadata_json'})
        return participant, sample

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
