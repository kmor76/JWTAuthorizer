from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
import jwt
import argparse
import yaml
import re

group_allowed = 'none'
upstream_host = ''
upstream_port = 8090
config = {}

class ProxyHTTPRequestHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.0'

    def do_POST(self):
        check(self, 'post')

    def do_GET(self):
        check(self, 'get')

    def do_DELETE(self):
        check(self, 'delete')

    def do_PATCH(self):
        check(self, 'patch')

def check(req, method):
    action_allowed=True
    req_header = req.headers
    token = req_header.get('authorization').replace('Bearer ', '')
    decoded = jwt.decode(token, options={"verify_signature": False})
    groups = decoded.get('groups')
    locations = config.get(method)
    print("checking path:",req.path,"groups:",groups,"method:",method)
    print("locations to check:",locations)
    if locations:
        for location_key in locations.keys():
            if bool(re.match(location_key,req.path)):
                action_allowed=False
                groups_value=locations.get(location_key)
                print("Location",req.path,"match with mask",location_key,"and required permissions",groups_value)
                for group_key in groups:
                    if group_key in groups_value:
                        print("Permission found:",group_key)
                        action_allowed=True
                        break
                break

    if action_allowed:
        do_proxy(req, method)
    else:
        req.send_response(403)
        req.end_headers()
        req.wfile.write(b'403')
        print("Denied!")
        return

def do_proxy(req, method):
    print(req.path)
    print(method)
    req_header = req.headers
    host = '{}:{}'.format(upstream_host, upstream_port)
    origin = 'http://{}:{}'.format(upstream_host, upstream_port)
    url = 'http://{}:{}{}'.format(upstream_host, upstream_port, req.path)
    req_header.replace_header('Host', host)
    if req_header.get('Referer') != None:
        req_header.replace_header('Referer', url)
    if req_header.get('Origin') != None:
        req_header.replace_header('Origin', origin)
    if method == 'get':
        resp = requests.get(url, headers=req_header, verify=False)
    if method == 'post':
        content_length = int(req.headers['Content-Length'])
        post_data = req.rfile.read(content_length)
        resp = requests.post(url, data=post_data, headers=req_header, verify=False)
    if method == 'patch':
        content_length = int(req.headers['Content-Length'])
        post_data = req.rfile.read(content_length)
        resp = requests.patch(url, data=post_data, headers=req_header, verify=False)
    if method == 'delete':
        resp = requests.delete(url, headers=req_header, verify=False)
    req.send_response(resp.status_code)
    for header in resp.headers:
        req.send_header(header, resp.headers.get(header))
    req.end_headers()
    req.wfile.write(resp.content)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('proxy_host', type=str, help='0.0.0.0')
    parser.add_argument('proxy_port', type=int, help='8081')
    parser.add_argument('upstream_host', type=str, help='upstream_ip')
    parser.add_argument('upstream_port', type=int, help='8080')
    parser.add_argument('config_path', type=str, help='config')
    args = parser.parse_args()
    upstream_host = args.upstream_host
    upstream_port = args.upstream_port
    config_path   = args.config_path
    print(args)
    with open(config_path, "r") as yamlfile:
        config = yaml.load(yamlfile, Loader=yaml.FullLoader)
        print("Loaded config:",config)

    server_address = (args.proxy_host, args.proxy_port)
    httpd = HTTPServer(server_address, ProxyHTTPRequestHandler)
    print('http server is running')
    httpd.serve_forever()
