# bagit-firecloud-lambda

This lambda accepts a POST with a bagit in the request body, and uploads TSVs from the bagit to FireCloud. When
FireCloud adds an endpoint that directly accepts a bagit, this lambda will be unnecessary.

A development instance is currently stood up at `https://egyjdjlme2.execute-api.us-west-2.amazonaws.com`.

## Using the service

```
curl -X POST --header "Authorization: Bearer <Google token>" -header "Content-type: application/octet-stream" --data @bagit.zip "https://egyjdjlme2.execute-api.us-west-2.amazonaws.com/api/exportBag?workspace=<workspace>&namespace=<namespace>" 
```

* Google token -- a Google oauth token. This is used when making the FireCloud API calls. The FireCloud API currently
requires that this token have the `https://www.googleapis.com/auth/devstorage.full_control` scope.
* bagit.zip -- A Bagit, zipped up. The Bagit currently must contain one TSV file, although it will be changed to 
accept two TSV files (see below).
* workspace -- The name of the FireCloud workspace. If it does not exist, this lambda will create the workspace.
* namespace -- The name of the FireCloud namespace. In the FireCloud UI, a namespace is called a `billing project`.
The namespace must already exist in FireCloud.

## The Bag

Currently the lambda expects one TSV file in the bag, and then splits it up into two TSV files, uploading each one in
order to FireCloud. The logic for splitting up the TSV assumes the format of the way Boardwalk currently exports
data, and does not belong in the lambda. Work is in progress to change this.

The lambda should expect a [bagit](https://en.wikipedia.org/wiki/BagIt), with its data directory containing two TSV
files, one with the participants and one with the samples. We need to finalize how the lambda will know which file is
participants and which one is samples.

## TODO

* Move TSV splitting logic into Boardwalk (see previous section).
* Should also support fetch.txt in bagit, where the TSVs are not directly in the bagit.
* Does it make sense to export into an existing workspace, or should the lambda always enforce a new workspace?
* Better error handling; utils.py assumes all http invocations are successful 
* Finalize the response body for success

