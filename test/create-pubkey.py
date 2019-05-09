import urllib2
import argparse
import json
import os
import sys
import logging

import scitokens

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

def main():
    
    parser = argparse.ArgumentParser(description='Create token and test endpoint.')
    parser.add_argument('--aud', dest='aud', help="Insert an audience")
    parser.add_argument('pubjwk', metavar='p', type=str,
                    help='The jwks public key')
    parser.add_argument('--nolog', dest='log', action='store_false', help="Do not print logs and token.")
    args = parser.parse_args()

    if args.log:
        logging.basicConfig(level=logging.INFO)
    
    private_key = None
    with open('private.pem', 'rb') as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
            backend=default_backend()
        )
    
    # Read in the public key to get the kid
    jwk_pub = ""
    with open(args.pubjwk, 'r') as jwk_pub_file:
        jwk_pub = json.load(jwk_pub_file)
    
    key_id = jwk_pub['keys'][0]['kid']

    token = scitokens.SciToken(key=private_key, key_id=key_id)
    token["scope"] = "read:/"
    
    if 'aud' in args and args.aud is not None:
        token["aud"] = args.aud
    
    token_str = token.serialize(issuer="https://localhost")
    headers = {"Authorization": "Bearer {0}".format(token_str)}
    try:
        request = urllib2.Request("http://localhost:8080/tmp/random.txt", headers=headers)
        contents = urllib2.urlopen(request).read()
    except urllib2.HTTPError:
        if args.log:
            for logdir in ["/var/log/httpd", "/var/log/xrootd/http"]:
                if not os.path.isdir(logdir): continue
                for fn in os.listdir(logdir):
                    fp = logdir+"/"+fn
                    if os.path.isfile(fp) and os.path.getsize(fp) > 0:
                        print >>sys.stderr, "-" * len(fp)
                        print >>sys.stderr, fp
                        print >>sys.stderr, "-" * len(fp)
                        os.system("tail -n 50 " + fp + " >&2")
                        print >>sys.stderr
        raise
    print contents,
    
    #request = urllib2.Request("http://localhost:8080/tmp/random.txt")
    #contents = urllib2.urlopen(request).read()
    #print contents,
    


if __name__ == "__main__":
    main()

