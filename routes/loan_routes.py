"""Loan management routes for application, list, edit, close, and approvals."""
from decimal import Decimal
from web import router, Request, Response
from routes.auth_routes import require_admin_auth
from repositories.branch_repository import BranchRepository
from repositories.loan_repository import LoanRepository
from repositories.instalment_repository import InstalmentRepository
from repositories.collection_repository import CollectionRepository
from services.loan_service import LoanService
from template_engine import template_engine

@router.get('/admin/loan')
@router.get('/admin/loan/add')
def loan_add_get(req: Request) -> Response:
    auth_check = require_admin_auth(req)
    if auth_check:
        return auth_check

    branches = BranchRepository.get_all()
    app_no = LoanService.get_next_application_no()
    context = {
        'user': req.user,
        'branch_list': branches,
        'app_no': app_no,
        'msg': req.get_flash('msg'),
        'errors': {},
        'form': {}
    }
    html_content = template_engine.render_file('admin/add-loan.html', context)
    return Response.html(html_content)

@router.post('/admin/loan')
@router.post('/admin/loan/add')
def loan_add_post(req: Request) -> Response:
    auth_check = require_admin_auth(req)
    if auth_check:
        return auth_check

    loan_id, errors = LoanService.create_loan(req.form_data)
    if errors:
        branches = BranchRepository.get_all()
        app_no = req.form_data.get('loan_application_no') or LoanService.get_next_application_no()
        error_html = "<div class='alert alert-danger alert-dismissible'><a href='#' class='close' data-dismiss='alert' aria-label='close'>&times;</a>" + "<br>".join(errors) + "</div>"
        context = {
            'user': req.user,
            'branch_list': branches,
            'app_no': app_no,
            'msg': error_html,
            'errors': {e.split()[0].lower(): e for e in errors},
            'form': req.form_data
        }
        return Response.html(template_engine.render_file('admin/add-loan.html', context))

    success_msg = '<div class="alert alert-success alert-dismissible"><a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a>Loan Added Successfully.</div>'
    req.set_flash('msg', success_msg)
    return Response.redirect('/admin/loan')

@router.get('/admin/loan/list')
def loan_list(req: Request) -> Response:
    auth_check = require_admin_auth(req)
    if auth_check:
        return auth_check

    loans = LoanRepository.get_all()
    total_loan_amount = 0.0
    total_collect_amount = 0.0

    for loan in loans:
        coll_count = CollectionRepository.count_by_loan_id(loan['loan_id'])
        loan['del_loan'] = 'Yes' if coll_count == 0 else 'No'
        total_loan_amount += float(loan['loan_amount'])
        total_collect_amount += float(loan['loan_intrest_amount'])

    context = {
        'user': req.user,
        'loan_list': loans,
        'total_loan_amount': total_loan_amount,
        'total_collect_amount': total_collect_amount,
        'msg': req.get_flash('msg')
    }
    html_content = template_engine.render_file('admin/loan-list.html', context)
    return Response.html(html_content)

@router.get('/admin/loan/edit/{loan_id}')
def loan_edit_get(req: Request, loan_id: str) -> Response:
    auth_check = require_admin_auth(req)
    if auth_check:
        return auth_check

    lid = int(loan_id)
    edit = LoanRepository.get_by_id(lid)
    if not edit:
        req.set_flash('msg', '<div class="alert alert-danger">Loan not found.</div>')
        return Response.redirect('/admin/loan/list')

    branches = BranchRepository.get_all()
    context = {
        'user': req.user,
        'edit': edit,
        'branch_list': branches,
        'msg': req.get_flash('msg'),
        'errors': {}
    }
    html_content = template_engine.render_file('admin/edit-loan.html', context)
    return Response.html(html_content)

@router.post('/admin/loan/edit/{loan_id}')
def loan_edit_post(req: Request, loan_id: str) -> Response:
    auth_check = require_admin_auth(req)
    if auth_check:
        return auth_check

    lid = int(loan_id)
    success, errors = LoanService.edit_loan(lid, req.form_data)
    if not success:
        edit = LoanRepository.get_by_id(lid)
        branches = BranchRepository.get_all()
        error_html = "<div class='alert alert-danger alert-dismissible'><a href='#' class='close' data-dismiss='alert' aria-label='close'>&times;</a>" + "<br>".join(errors) + "</div>"
        context = {
            'user': req.user,
            'edit': edit,
            'branch_list': branches,
            'msg': error_html,
            'errors': {}
        }
        return Response.html(template_engine.render_file('admin/edit-loan.html', context))

    success_msg = '<div class="alert alert-success alert-dismissible"><a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a>Loan Edit Successfully.</div>'
    req.set_flash('msg', success_msg)
    return Response.redirect(f'/admin/loan/edit/{lid}')

@router.get('/admin/loan/delete/{loan_id}')
def loan_delete(req: Request, loan_id: str) -> Response:
    auth_check = require_admin_auth(req)
    if auth_check:
        return auth_check

    lid = int(loan_id)
    success, msg = LoanService.delete_loan(lid)
    alert_class = "alert-success" if success else "alert-danger"
    req.set_flash('msg', f'<div class="alert {alert_class} alert-dismissible"><a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a>{msg}</div>')
    return Response.redirect('/admin/loan/list')

@router.post('/admin/loan/approveLoan')
def loan_approve(req: Request) -> Response:
    loan_id = req.form_data.get('loan_id') or (req.json_data.get('loan_id') if req.json_data else None)
    if loan_id:
        LoanRepository.set_status(int(loan_id), 1)
    return Response.json({'status': 200})

@router.post('/admin/loan/unapproveLoan')
def loan_unapprove(req: Request) -> Response:
    loan_id = req.form_data.get('loan_id') or (req.json_data.get('loan_id') if req.json_data else None)
    if loan_id:
        LoanRepository.set_status(int(loan_id), 0)
    return Response.json({'status': 200})

@router.get('/admin/loan/instalment/{loan_id}')
def loan_instalment_view(req: Request, loan_id: str) -> Response:
    auth_check = require_admin_auth(req)
    if auth_check:
        return auth_check

    lid = int(loan_id)
    loan = LoanRepository.get_by_id(lid)
    if not loan:
        return Response.redirect('/admin/loan/list')

    instalments = InstalmentRepository.get_by_loan_id(lid)
    context = {
        'user': req.user,
        'loan': loan,
        'instalment': instalments
    }
    html_content = template_engine.render_file('admin/instalment-list.html', context)
    return Response.html(html_content)

@router.get('/admin/loan/close')
def loan_close_get(req: Request) -> Response:
    auth_check = require_admin_auth(req)
    if auth_check:
        return auth_check

    loans = LoanRepository.get_dropdown_list()
    context = {
        'user': req.user,
        'loan_list': loans,
        'msg': req.get_flash('msg'),
        'errors': {}
    }
    html_content = template_engine.render_file('admin/loan-close.html', context)
    return Response.html(html_content)

@router.post('/admin/loan/close')
def loan_close_post(req: Request) -> Response:
    auth_check = require_admin_auth(req)
    if auth_check:
        return auth_check

    loan_id_str = req.form_data.get('loan_id', '').strip()
    due_amt_str = req.form_data.get('due_amount', '').strip()
    payment_date = req.form_data.get('payment_date', '').strip()
    remark = req.form_data.get('remark', '').strip()

    errors = {}
    if not loan_id_str:
        errors['loan_id'] = 'Client Name/ Application No. is required.'
    if not due_amt_str:
        errors['due_amount'] = 'Due Amount is required.'
    if not payment_date:
        errors['payment_date'] = 'Date is required.'

    if errors:
        loans = LoanRepository.get_dropdown_list()
        context = {
            'user': req.user,
            'loan_list': loans,
            'msg': '',
            'errors': errors
        }
        return Response.html(template_engine.render_file('admin/loan-close.html', context))

    try:
        due_amount = Decimal(due_amt_str)
        success, msg = LoanService.close_loan(int(loan_id_str), due_amount, payment_date, remark)
        alert_class = "alert-success" if success else "alert-danger"
        req.set_flash('msg', f'<div class="alert {alert_class} alert-dismissible"><a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a>{msg}</div>')
    except Exception as e:
        req.set_flash('msg', f'<div class="alert alert-danger">Error: {e}</div>')

    return Response.redirect('/admin/loan/close')
