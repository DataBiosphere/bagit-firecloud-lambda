#!/usr/bin/env python

from chalice import Response

# Standalone utility functions.

def requests_response_to_chalice_Response(response):
    """Takes some attributes from a request response object and creates
    a Chalice Response object from it.
    
    :param response: (response object) from requests module 
    :return: Chalice module Response object 
    """

    body, headers = check_headers(response)
    return Response(body=body,
                    headers=headers,
                    status_code=response.status_code)

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
