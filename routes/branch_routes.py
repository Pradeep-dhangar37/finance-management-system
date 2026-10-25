"""Branch management routes."""
from datetime import date
from web import router, Request, Response
from routes.auth_routes import require_admin_auth
from repositories.branch_repository import BranchRepository
from template_engine import template_engine

@router.get('/admin/branch/add')
def branch_add_get(req: Request) -> Response:
    auth_check = require_admin_auth(req)
    if auth_check:
        return auth_check

    branches = BranchRepository.get_all()
    context = {
        'user': req.user,
        'branch_list': branches,
        'branch_name': '',
        'msg': req.get_flash('msg'),
        'errors': {}
    }
    html_content = template_engine.render_file('admin/branch.html', context)
    return Response.html(html_content)

@router.post('/admin/branch/add')
def branch_add_post(req: Request) -> Response:
    auth_check = require_admin_auth(req)
    if auth_check:
        return auth_check

    branch_name = req.form_data.get('branch_name', '').strip()
    errors = {}
    if not branch_name:
        errors['branch_name'] = 'Branch Name is required.'
    else:
        existing = BranchRepository.get_by_name(branch_name)
        if existing:
            errors['branch_name'] = 'The Branch Name is already taken.'

    if errors:
        branches = BranchRepository.get_all()
        context = {
            'user': req.user,
            'branch_list': branches,
            'branch_name': branch_name,
            'msg': '',
            'errors': errors
        }
        return Response.html(template_engine.render_file('admin/branch.html', context))

    BranchRepository.create(branch_name, date.today().strftime('%Y-%m-%d'))
    success_msg = '<div class="alert alert-success alert-dismissible"><a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a>Branch Added Successfully.</div>'
    req.set_flash('msg', success_msg)
    return Response.redirect('/admin/branch/add')

@router.get('/admin/branch/edit/{branch_id}')
def branch_edit_get(req: Request, branch_id: str) -> Response:
    auth_check = require_admin_auth(req)
    if auth_check:
        return auth_check

    bid = int(branch_id)
    edit = BranchRepository.get_by_id(bid)
    if not edit:
        req.set_flash('msg', '<div class="alert alert-danger">Branch not found.</div>')
        return Response.redirect('/admin/branch/add')

    branches = BranchRepository.get_all()
    context = {
        'user': req.user,
        'edit': edit,
        'branch_list': branches,
        'branch_name': edit['branch_name'],
        'msg': req.get_flash('msg'),
        'errors': {}
    }
    return Response.html(template_engine.render_file('admin/edit-branch.html', context))

@router.post('/admin/branch/edit/{branch_id}')
def branch_edit_post(req: Request, branch_id: str) -> Response:
    auth_check = require_admin_auth(req)
    if auth_check:
        return auth_check

    bid = int(branch_id)
    edit = BranchRepository.get_by_id(bid)
    if not edit:
        return Response.redirect('/admin/branch/add')

    branch_name = req.form_data.get('branch_name', '').strip()
    errors = {}
    if not branch_name:
        errors['branch_name'] = 'Branch Name is required.'
    elif branch_name != edit['branch_name']:
        existing = BranchRepository.get_by_name(branch_name)
        if existing and existing['branch_id'] != bid:
            errors['branch_name'] = 'The Branch Name is already taken.'

    if errors:
        branches = BranchRepository.get_all()
        context = {
            'user': req.user,
            'edit': edit,
            'branch_list': branches,
            'branch_name': branch_name,
            'msg': '',
            'errors': errors
        }
        return Response.html(template_engine.render_file('admin/edit-branch.html', context))

    BranchRepository.update(bid, branch_name)
    success_msg = '<div class="alert alert-success alert-dismissible"><a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a>Branch Edit Successfully.</div>'
    req.set_flash('msg', success_msg)
    return Response.redirect(f'/admin/branch/edit/{bid}')
