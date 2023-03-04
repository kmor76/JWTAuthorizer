from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
import jwt
import argparse

group_allowed='none'
upstream_host=''
upstream_port=8090

class ProxyHTTPRequestHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.0'

    def do_POST(self):
        check(self)

    def do_GET(self):
        check(self)

    def do_DELETE(self):
        check(self)

def check(req):
    req_header = req.headers
    token = req_header.get('authorization').replace('Bearer ', '')
    decoded = jwt.decode(token, options={"verify_signature": False})
    groups = decoded.get('groups')
    if group_allowed in groups:
        url = 'http://{}:{}{}'.format(upstream_host, upstream_port, req.path)
        resp = requests.get(url, headers=req_header, verify=False)
        req.send_response(resp.status_code)
        for header in resp.headers:
            req.send_header(header, resp.headers.get(header))
        req.end_headers()
        req.wfile.write(resp.content)
    else:
        req.send_response(403)
        req.end_headers()
        req.wfile.write(b'403')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('proxy_host', type=str, help='0.0.0.0')
    parser.add_argument('proxy_port', type=int, help='8081')
    parser.add_argument('upstream_host', type=str, help='upstream_ip')
    parser.add_argument('upstream_port', type=int, help='8080')
    parser.add_argument('group_allowed', type=str, help='admins')
    args = parser.parse_args()
    group_allowed = args.group_allowed
    upstream_host = args.upstream_host
    upstream_port = args.upstream_port
    print(args)
    server_address = (args.proxy_host, args.proxy_port)
    httpd = HTTPServer(server_address, ProxyHTTPRequestHandler)
    print('http server is running')
    httpd.serve_forever()
