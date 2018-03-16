#!/usr/bin/env python

import unittest
import os
import pandas as pd
from pandas.util.testing import assert_frame_equal
from pandas.util.testing import assert_series_equal
#from pandas.util.testing import assert
from chalicelib.utils import ManifestIO

base_path = os.path.abspath(os.path.dirname(__file__))

class TestManifestIO(unittest.TestCase):

    def test_all_facets(self):
        i = 2
        self.assertEqual(i, 2, msg='well done')

    def test_transform_df(self):

        # Create Pandas dataframes of all
        tsv_name = '{}/test_participant.tsv'.format(base_path)
        df_participant = pd.read_table(tsv_name)
        tsv_name = '{}/test_sample.tsv'.format(base_path)
        df_sample = pd.read_table(tsv_name)
        tsv_name = '{}/test_manifest.tsv'.format(base_path)
        df_manifest = pd.read_table(tsv_name)

        manifest_io = ManifestIO(tsv_name)
        participant, sample = manifest_io._transform_df()

        assert_series_equal(participant, df_participant)
        # assert_frame_equal(sample, df_sample)


if __name__ == '__main__':
    unittest.main()