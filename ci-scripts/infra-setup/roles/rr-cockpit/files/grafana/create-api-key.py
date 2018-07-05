#!/usr/bin/env python

import argparse
import requests

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description="Print created api key")

    parser.add_argument('--url', required=True)
    parser.add_argument('--key-name', required=True)

    args = parser.parse_args()

    response=requests.post(args.url + "/api/auth/keys", headers={"Content-Type": "application/json"}, data='{"name":"${}", "role": "Admin"}'.format(args.key_name))

    print(response.content)
