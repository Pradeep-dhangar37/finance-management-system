from typing import Optional
"""Authentication routes for Admin and App portals."""
from web import router, Request, Response
from security import verify_password, hash_password, session_manager
from repositories.user_repository import UserRepository
from template_engine import template_engine
from config import Config

def require_admin_auth(req: Request) -> Optional[Response]:
    """Ensure user is logged into admin portal."""
    if not req.user:
        return Response.redirect('/admin/login')
    return None

def require_app_auth(req: Request) -> Optional[Response]:
    """Ensure agent is logged into app portal."""
    if not req.appuser:
        return Response.redirect('/app/login')
    return None

# ==================== ADMIN AUTH ====================

@router.get('/admin/login')
def admin_login_get(req: Request) -> Response:
    if req.user:
        return Response.redirect('/admin/dashboard')
    msg = req.get_flash('msg')
    html_content = template_engine.render_file('admin/login.html', {
        'msg': msg,
        'email': '',
        'errors': {}
    })
    return Response.html(html_content)

@router.post('/admin/login')
def admin_login_post(req: Request) -> Response:
    email = req.form_data.get('email', '').strip()
    password = req.form_data.get('password', '').strip()
    errors = {}
    if not email:
        errors['email'] = 'Email is required.'
    if not password:
        errors['password'] = 'Password is required.'

    if errors:
        html_content = template_engine.render_file('admin/login.html', {
            'msg': '',
            'email': email,
            'errors': errors
        })
        return Response.html(html_content)

    user = UserRepository.get_by_email(email)
    if user and verify_password(password, user['password']):
        user_data = {'user_id': user['user_id'], 'username': user['username'], 'email': user['email']}
        session_id = session_manager.create_session(user_data, is_app=False)
        resp = Response.redirect('/admin/dashboard')
        resp.set_cookie(Config.SESSION_COOKIE_NAME, session_id)
        return resp
    else:
        fail_msg = '<div class="alert alert-danger alert-dismissible"><a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a>Invalid Email And Password.</div>'
        html_content = template_engine.render_file('admin/login.html', {
            'msg': fail_msg,
            'email': email,
            'errors': {}
        })
        return Response.html(html_content)

@router.get('/admin/login/logout')
@router.get('/admin/logout')
def admin_logout(req: Request) -> Response:
    session_manager.destroy_session(req.session_id, is_app=False)
    resp = Response.redirect('/admin/login')
    return resp

@router.get('/admin/dashboard/changePassword')
@router.get('/admin/dashboard/changepassword')
def change_password_get(req: Request) -> Response:
    auth_check = require_admin_auth(req)
    if auth_check:
        return auth_check
    html_content = template_engine.render_file('admin/change-password.html', {
        'user': req.user,
        'msg': req.get_flash('msg'),
        'errors': {}
    })
    return Response.html(html_content)

@router.post('/admin/dashboard/changePassword')
@router.post('/admin/dashboard/changepassword')
def change_password_post(req: Request) -> Response:
    auth_check = require_admin_auth(req)
    if auth_check:
        return auth_check

    pwd = req.form_data.get('password', '').strip()
    cpwd = req.form_data.get('cpassword', '').strip()
    errors = {}
    if not pwd:
        errors['password'] = 'Password is required.'
    if not cpwd:
        errors['cpassword'] = 'Confirm Password is required.'
    elif pwd != cpwd:
        errors['cpassword'] = 'Passwords do not match.'

    if errors:
        html_content = template_engine.render_file('admin/change-password.html', {
            'user': req.user,
            'msg': '',
            'errors': errors
        })
        return Response.html(html_content)

    new_hash = hash_password(pwd)
    UserRepository.update_password(req.user['user_id'], new_hash)
    success_msg = '<div class="alert alert-success alert-dismissible"><a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a>Password Change Successfully.</div>'
    req.set_flash('msg', success_msg)
    return Response.redirect('/admin/dashboard/changePassword')

# ==================== APP AUTH ====================

@router.get('/app/login')
def app_login_get(req: Request) -> Response:
    if req.appuser:
        return Response.redirect('/app/dashboard')
    html_content = template_engine.render_file('app/login.html', {
        'msg': req.get_flash('msg'),
        'email': '',
        'errors': {}
    })
    return Response.html(html_content)

@router.post('/app/login')
def app_login_post(req: Request) -> Response:
    email = req.form_data.get('email', '').strip()
    password = req.form_data.get('password', '').strip()
    errors = {}
    if not email:
        errors['email'] = 'Email is required.'
    if not password:
        errors['password'] = 'Password is required.'

    if errors:
        html_content = template_engine.render_file('app/login.html', {
            'msg': '',
            'email': email,
            'errors': errors
        })
        return Response.html(html_content)

    user = UserRepository.get_by_email(email)
    if user and verify_password(password, user['password']):
        user_data = {'user_id': user['user_id'], 'username': user['username'], 'email': user['email']}
        if req.session_id:
            session_manager.set_user(req.session_id, user_data, is_app=True)
            session_id = req.session_id
        else:
            session_id = session_manager.create_session(user_data, is_app=True)
        resp = Response.redirect('/app/dashboard')
        resp.set_cookie(Config.SESSION_COOKIE_NAME, session_id)
        return resp
    else:
        fail_msg = '<div class="alert alert-danger alert-dismissible"><a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a>Invalid Email And Password.</div>'
        html_content = template_engine.render_file('app/login.html', {
            'msg': fail_msg,
            'email': email,
            'errors': {}
        })
        return Response.html(html_content)

@router.get('/app/login/logout')
@router.get('/app/logout')
def app_logout(req: Request) -> Response:
    session_manager.destroy_session(req.session_id, is_app=True)
    resp = Response.redirect('/app/login')
    return resp
