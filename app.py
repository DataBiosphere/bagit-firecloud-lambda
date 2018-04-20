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
    """Expects a compressed (zipped) BagIt structure that
    contains two TSV files named  "participant.tsv" and
    "sample.tsv" in its "data" sub-directory. It creates
    a new workspace in a FireCloud namespace, and uploads
    the data into it.
    Aborts execution and returns HTTP body back to client if any 
    request operation fails."""
    req_body = app.current_request.raw_body
    req_query_params = app.current_request.query_params
    req_headers = app.current_request.headers
    os.chdir('/tmp')
    with zipfile.ZipFile(io.BytesIO(req_body), 'r') as archive:
        archive.extractall()
    data = {
        'participant': '/tmp/manifest/data/participant.tsv',
        'sample': '/tmp/manifest/data/sample.tsv'
    }
    url = 'https://api.firecloud.org/api/workspaces'
    workspace = req_query_params['workspace']
    namespace = req_query_params['namespace']
    auth = req_headers['Authorization']

    manifest_io = ManifestIO(data, url, workspace, namespace, auth)
    # Check whether the workspace exists in this namespace, otherwise create it.
    r_check_workspace = manifest_io.workspace_exists()
    resp = manifest_io.manage_workspace(r_check_workspace)
    if resp:
        return resp
    resp = manifest_io.upload_files(['participant', 'sample'])
    if resp:
        return resp
    else:
        return Response(body=manifest_io.status_codes,
                    headers={'Content-Type': 'application/json'})
