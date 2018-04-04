# bagit-firecloud-lambda

This lambda accepts a POST with a BagIt in the request body, and uploads TSVs from the bagit to FireCloud. When FireCloud adds an endpoint that directly accepts a BagIt, this lambda will be unnecessary.

A staging instance is currently stood up at `https://vzltaytzg4.execute-api.us-west-2.amazonaws.com/api/`.

## Using the service

```
curl -X POST --header "Authorization: Bearer <Google token>" -header "Content-type: application/octet-stream" --data @bagit.zip "https://vzltaytzg4.execute-api.us-west-2.amazonaws.com/api/exportBag?workspace=<workspace>&namespace=<namespace>" 
```

* Google token -- a Google oauth token. This is used when making the FireCloud API calls. The FireCloud API currently
requires that this token have the `https://www.googleapis.com/auth/devstorage.full_control` scope.
* bagit.zip -- A BagIt, zipped up.
* workspace -- The name of the FireCloud workspace. If it does not exist, this lambda will create the workspace.
* namespace -- The name of the FireCloud namespace. In the FireCloud UI, a namespace is called a `billing project`.
The namespace must already exist in FireCloud.

## The Bag

Currently the lambda expects a [BagIt](https://en.wikipedia.org/wiki/BagIt) containing two TSV files, `participant.tsv` and `sample.tsv`, which it  uploads in to FireCloud in that order.
## TODO

* Should also support fetch.txt in BagIt, where the TSVs are not directly in the BagIt .
* Better error handling; utils.py assumes all http invocations are successful 
* Test TSV file content (i.e., which one contains `participant` and `sample` data) so that naming of TSV files can be left to the user. 
* Finalize the response body for success
