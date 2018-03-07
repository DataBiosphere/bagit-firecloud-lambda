import logging
import os
import zipfile
import io
from chalice import Chalice, Response
from chalicelib.utils import ManifestIO

app = Chalice(app_name='bagit-firecloud-lambda')
app.debug = True
app.log.setLevel(logging.DEBUG)


@app.route('/exportBag',
           methods=['POST'],
           content_types=['application/octet-stream'])
def exportBag():
    req_body = app.current_request.raw_body
    req_query_params = app.current_request.query_params
    req_headers = app.current_request.headers
    os.chdir('/tmp')
    with zipfile.ZipFile(io.BytesIO(req_body), 'r') as archive:
        archive.extractall()
    tsv_fname = '/tmp/manifest_bag/data/manifest.tsv'
    workspace = req_query_params['workspace']
    namespace = req_query_params['namespace']
    url = 'https://api.firecloud.org/api/workspaces'
    auth = req_headers['Authorization']
    manifest_io = ManifestIO(tsv_fname, url, workspace, namespace, auth)
    statusCode = manifest_io.import_tsv_to_fc()
    return Response(body=statusCode,
                    status_code=200,
                    headers={'Content-Type': 'application/json',
                             'Accept': 'application/json'})
