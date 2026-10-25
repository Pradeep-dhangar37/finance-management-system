"""
Lightweight HTTP request/response abstractions and router for Core Python http.server.
Handles URL dispatching, cookie parsing, sessions, flash messages, and form parsing.
"""
import json
import mimetypes
import os
import urllib.parse
from http import cookies
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List, Tuple
from config import Config
from security import session_manager

class Request:
    def __init__(self, method: str, full_path: str, headers: Dict[str, str], body_bytes: bytes, client_address: Tuple[str, int]):
        self.method = method.upper()
        self.client_address = client_address
        parsed = urllib.parse.urlparse(full_path)
        self.path = parsed.path
        self.query_string = parsed.query
        self.query_params = {k: v[0] if len(v) == 1 else v for k, v in urllib.parse.parse_qs(parsed.query).items()}
        self.headers = headers
        self.body_bytes = body_bytes
        self.cookies: Dict[str, str] = {}
        self._parse_cookies()
        self.form_data: Dict[str, Any] = {}
        self.json_data: Optional[Dict[str, Any]] = None
        self._parse_body()
        
        # Session & authentication
        import secrets
        self.session_id = self.cookies.get(Config.SESSION_COOKIE_NAME)
        if not self.session_id:
            self.session_id = secrets.token_urlsafe(32)
            self.new_session = True
        else:
            self.new_session = False
        self.session = session_manager.get_session(self.session_id)
        self.user = session_manager.get_user(self.session_id, is_app=False)
        self.appuser = session_manager.get_user(self.session_id, is_app=True)

    def _parse_cookies(self):
        cookie_header = self.headers.get('Cookie') or self.headers.get('cookie')
        if cookie_header:
            c = cookies.SimpleCookie()
            try:
                c.load(cookie_header)
                self.cookies = {k: v.value for k, v in c.items()}
            except Exception:
                pass

    def _parse_body(self):
        content_type = self.headers.get('Content-Type') or self.headers.get('content-type') or ''
        if not self.body_bytes:
            return
        if 'application/json' in content_type:
            try:
                self.json_data = json.loads(self.body_bytes.decode('utf-8'))
            except Exception:
                self.json_data = {}
        elif 'application/x-www-form-urlencoded' in content_type or 'multipart/form-data' in content_type:
            try:
                decoded = self.body_bytes.decode('utf-8', errors='replace')
                parsed_form = urllib.parse.parse_qs(decoded)
                self.form_data = {k: v[0] if len(v) == 1 else v for k, v in parsed_form.items()}
            except Exception:
                self.form_data = {}

    def get_flash(self, key: str = 'msg') -> Optional[str]:
        return session_manager.get_flash(self.session_id, key)

    def set_flash(self, key: str, message: str):
        session_manager.set_flash(self.session_id, key, message)

class Response:
    def __init__(self, body: Any = "", status: int = 200, content_type: str = "text/html; charset=utf-8", headers: Optional[Dict[str, str]] = None):
        self.status = status
        self.content_type = content_type
        self.headers = headers or {}
        self.headers['Content-Type'] = content_type
        self.cookies_to_set: List[str] = []

        if isinstance(body, str):
            self.body_bytes = body.encode('utf-8')
        elif isinstance(body, bytes):
            self.body_bytes = body
        else:
            self.body_bytes = str(body).encode('utf-8')
        self.headers['Content-Length'] = str(len(self.body_bytes))

    def set_cookie(self, name: str, value: str, max_age: int = 86400, path: str = "/", httponly: bool = True):
        cookie = f"{name}={value}; Path={path}; Max-Age={max_age}; SameSite=Lax"
        if httponly:
            cookie += "; HttpOnly"
        self.cookies_to_set.append(cookie)

    @classmethod
    def redirect(cls, location: str, status: int = 302, flash_key: str = None, flash_msg: str = None, session_id: str = None):
        if flash_key and flash_msg and session_id:
            session_manager.set_flash(session_id, flash_key, flash_msg)
        resp = cls("", status=status)
        resp.headers['Location'] = location
        return resp

    @classmethod
    def json(cls, data: Any, status: int = 200):
        body = json.dumps(data)
        return cls(body, status=status, content_type="application/json")

    @classmethod
    def html(cls, html_str: str, status: int = 200):
        return cls(html_str, status=status, content_type="text/html; charset=utf-8")


class Router:
    def __init__(self):
        # List of (method, regex_pattern, handler, param_names)
        self.routes: List[Tuple[str, Any, Callable, List[str]]] = []

    def add(self, method: str, pattern: str, handler: Callable):
        import re
        param_names = []
        # Convert path pattern like /admin/loan/edit/{loan_id} to regex
        def repl(match):
            param_names.append(match.group(1))
            return r"([^/]+)"
        regex_str = "^" + re.sub(r"\{([a-zA-Z0-9_]+)\}", repl, pattern) + "$"
        regex = re.compile(regex_str)
        self.routes.append((method.upper(), regex, handler, param_names))

    def get(self, pattern: str):
        def decorator(handler: Callable):
            self.add("GET", pattern, handler)
            return handler
        return decorator

    def post(self, pattern: str):
        def decorator(handler: Callable):
            self.add("POST", pattern, handler)
            return handler
        return decorator

    def match(self, method: str, path: str) -> Tuple[Optional[Callable], Dict[str, str]]:
        # Normalize trailing slash except root
        norm_path = path.rstrip('/') if len(path) > 1 else path
        effective_method = "GET" if method.upper() == "HEAD" else method.upper()
        for m, regex, handler, param_names in self.routes:
            if m == effective_method:
                match = regex.match(norm_path)
                if match:
                    kwargs = dict(zip(param_names, match.groups()))
                    return handler, kwargs
        return None, {}

router = Router()
