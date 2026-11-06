from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        html = "<html><body><h2>BvAi Vercel Deployment</h2><p>Serverless handler is working.</p></body></html>"
        self.wfile.write(html.encode('utf-8'))
        return
