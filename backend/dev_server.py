# dev_server.py  — solo para desarrollo local, no sube a AWS
from http.server import HTTPServer, BaseHTTPRequestHandler
import json, sys
sys.path.insert(0, 'lambdas/balance')
import handler as balance
sys.path.insert(0, 'lambdas/ingreso')
import handler as ingreso

class MockServer(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/balance':
            evento = {
                'requestContext': {'authorizer': {'claims': {'sub': 'user-local'}}}
            }
            resp = balance.lambda_handler(evento, None)
            self._send(resp)

    def do_POST(self):
        length = int(self.headers['Content-Length'])
        body   = self.rfile.read(length).decode()
        if self.path == '/ingreso':
            evento = {
                'body': body,
                'requestContext': {'authorizer': {'claims': {'sub': 'user-local'}}}
            }
            resp = ingreso.lambda_handler(evento, None)
            self._send(resp)

    def _send(self, resp):
        self.send_response(resp.get('statusCode', 200))
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(resp['body'].encode())

    def log_message(self, *args): pass  # silencia logs de HTTP

if __name__ == '__main__':
    print("Servidor local en http://localhost:8080")
    HTTPServer(('localhost', 8080), MockServer).serve_forever()