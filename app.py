#!/usr/bin/env python3
"""
Main Application Entrypoint for Astha Finance Management System.
Uses Python standard library http.server.ThreadingHTTPServer without any external web frameworks.
"""
import argparse
import logging
import mimetypes
import os
import sys
import urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# Load config and core modules
from config import Config
from db import Database
from web import router, Request, Response
from security import session_manager

# Import all route modules to register HTTP endpoints with router
from routes import (
    auth_routes,
    dashboard_routes,
    branch_routes,
    loan_routes,
    collection_routes,
    report_routes,
    app_routes
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger('financemanagement')

# Initialize mimetypes
mimetypes.init()
mimetypes.add_type('font/woff2', '.woff2')
mimetypes.add_type('font/woff', '.woff')
mimetypes.add_type('font/ttf', '.ttf')
mimetypes.add_type('text/css', '.css')
mimetypes.add_type('application/javascript', '.js')


class FinanceHTTPHandler(BaseHTTPRequestHandler):
    """Custom HTTP Request Handler routing dynamic endpoints and serving static assets."""
    server_version = "AsthaFinanceCore/1.0"

    def log_message(self, format, *args):
        logger.info("%s - - [%s] %s" % (self.client_address[0], self.log_date_time_string(), format % args))

    def do_GET(self):
        self.handle_request('GET')

    def do_POST(self):
        self.handle_request('POST')

    def do_HEAD(self):
        self.handle_request('HEAD')

    def handle_request(self, method: str):
        # 1. Parse incoming request path
        parsed_url = urllib.parse.urlparse(self.path)
        raw_path = parsed_url.path

        # 2. Check if this is a static asset request
        if raw_path.startswith('/static/'):
            self.serve_static(raw_path[8:])  # strip '/static/'
            return

        # 3. Read body bytes for POST/PUT requests
        body_bytes = b''
        content_length_str = self.headers.get('Content-Length') or self.headers.get('content-length')
        if content_length_str:
            try:
                content_length = int(content_length_str)
                body_bytes = self.rfile.read(content_length)
            except Exception as e:
                logger.warning("Failed to read body bytes: %s", e)
                body_bytes = b''

        # 4. Construct Request wrapper
        headers_dict = {k: v for k, v in self.headers.items()}
        req = Request(
            method=method,
            full_path=self.path,
            headers=headers_dict,
            body_bytes=body_bytes,
            client_address=self.client_address
        )

        # 5. Route dispatch
        handler, params = router.match(method, req.path)

        if not handler:
            self.send_not_found(req.path)
            return

        try:
            # Execute handler with route parameters if any
            if params:
                resp = handler(req, **params)
            else:
                resp = handler(req)

            # Ensure response object
            if not isinstance(resp, Response):
                resp = Response(resp)

            # Check if session cookie needs to be set
            if getattr(req, 'new_session', False) and req.session_id:
                # If flash or session was touched
                if session_manager.get_session(req.session_id):
                    resp.set_cookie(Config.SESSION_COOKIE_NAME, req.session_id)

            self.send_response_object(resp, head_only=(method == 'HEAD'))

        except Exception as e:
            logger.exception("Internal error processing request %s %s: %s", method, req.path, e)
            self.send_internal_error(str(e))

    def serve_static(self, rel_path: str):
        """Safely serve static files with MIME type detection and path traversal check."""
        try:
            # Decode URL components
            decoded_path = urllib.parse.unquote(rel_path.lstrip('/'))
            file_path = (Path(Config.STATIC_DIR) / decoded_path).resolve()
            static_root = Path(Config.STATIC_DIR).resolve()

            # Prevent directory traversal
            if not str(file_path).startswith(str(static_root)):
                self.send_error(403, "Access Forbidden")
                return

            if not file_path.is_file():
                self.send_error(404, "Static File Not Found")
                return

            content_type, _ = mimetypes.guess_type(str(file_path))
            if not content_type:
                content_type = "application/octet-stream"

            file_size = file_path.stat().st_size
            with open(file_path, 'rb') as f:
                content = f.read()

            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(file_size))
            self.send_header('Cache-Control', 'public, max-age=86400')
            self.end_headers()
            self.wfile.write(content)

        except Exception as e:
            logger.error("Error serving static file %s: %s", rel_path, e)
            self.send_error(500, "Internal Server Error")

    def send_response_object(self, resp: Response, head_only: bool = False):
        """Write HTTP headers and response body to the client socket."""
        self.send_response(resp.status)
        for h_key, h_val in resp.headers.items():
            self.send_header(h_key, h_val)

        for cookie in resp.cookies_to_set:
            self.send_header('Set-Cookie', cookie)

        self.end_headers()
        if not head_only:
            self.wfile.write(resp.body_bytes)

    def send_not_found(self, path: str):
        """Send custom 404 Not Found page."""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>404 Not Found - Astha Finance</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; text-align: center; padding: 50px; background: #f4f6f9; color: #333; }}
        .box {{ max-width: 500px; margin: auto; background: #fff; padding: 40px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        h1 {{ font-size: 72px; margin: 0; color: #3a4094; }}
        h2 {{ margin-top: 10px; }}
        p {{ color: #666; }}
        a {{ display: inline-block; margin-top: 20px; padding: 10px 20px; background: #3a4094; color: #fff; text-decoration: none; border-radius: 4px; }}
    </style>
</head>
<body>
    <div class="box">
        <h1>404</h1>
        <h2>Page Not Found</h2>
        <p>The requested URL <code>{path}</code> was not found on this server.</p>
        <a href="/admin">Return to Dashboard</a>
    </div>
</body>
</html>"""
        resp = Response.html(html, status=404)
        self.send_response_object(resp)

    def send_internal_error(self, err_msg: str):
        """Send custom 500 Internal Server Error page."""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>500 Server Error - Astha Finance</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; text-align: center; padding: 50px; background: #f4f6f9; color: #333; }}
        .box {{ max-width: 550px; margin: auto; background: #fff; padding: 40px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        h1 {{ font-size: 72px; margin: 0; color: #d9534f; }}
        h2 {{ margin-top: 10px; }}
        p {{ color: #666; }}
        a {{ display: inline-block; margin-top: 20px; padding: 10px 20px; background: #3a4094; color: #fff; text-decoration: none; border-radius: 4px; }}
    </style>
</head>
<body>
    <div class="box">
        <h1>500</h1>
        <h2>Internal Server Error</h2>
        <p>An unexpected error occurred while processing your request. Please try again or contact support.</p>
        <a href="/admin">Return to Dashboard</a>
    </div>
</body>
</html>"""
        resp = Response.html(html, status=500)
        self.send_response_object(resp)


def print_banner(host: str, port: int):
    banner = f"""
========================================================================
    ASTHA FINANCE MANAGEMENT SYSTEM (CORE PYTHON & MYSQL 8)
========================================================================
  [+] Language: Python 3 Standard Library (http.server.ThreadingHTTPServer)
  [+] Database: MySQL 8 (host: {Config.DB_HOST}:{Config.DB_PORT}, db: {Config.DB_NAME})
  [+] Web Server: http://{host}:{port}
  [+] Admin Portal: http://{host}:{port}/admin/login
  [+] Mobile Agent: http://{host}:{port}/app/login
  [+] Static Assets: {Config.STATIC_DIR}
  [+] Templates: {Config.TEMPLATES_DIR}
========================================================================
    Press Ctrl+C to stop the server gracefully.
========================================================================
"""
    print(banner)


def run_server(host: str = Config.HOST, port: int = Config.PORT):
    # Verify database connectivity
    print(f"Connecting to MySQL database '{Config.DB_NAME}' at {Config.DB_HOST}:{Config.DB_PORT}...")
    if Database.ping():
        print("  [SUCCESS] Database connection established.")
    else:
        print("  [WARNING] Could not connect to MySQL database.")
        print(f"  Please ensure MySQL is running and database '{Config.DB_NAME}' is initialized.")
        print("  Run schema: mysql -u root -p < sql/schema.sql")

    server_address = (host, port)
    httpd = ThreadingHTTPServer(server_address, FinanceHTTPHandler)
    print_banner(host, port)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[INFO] Stopping Astha Finance server...")
        httpd.server_close()
        print("[INFO] Server stopped successfully.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Astha Finance Management Web Server")
    parser.add_argument('--host', type=str, default=Config.HOST, help=f"Host to bind (default: {Config.HOST})")
    parser.add_argument('--port', type=int, default=Config.PORT, help=f"Port to bind (default: {Config.PORT})")
    args = parser.parse_args()

    run_server(host=args.host, port=args.port)
