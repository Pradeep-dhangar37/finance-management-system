"""Mobile Agent / App Portal routes."""
from datetime import date
from decimal import Decimal
from web import router, Request, Response
from routes.auth_routes import require_app_auth
from repositories.loan_repository import LoanRepository
from repositories.instalment_repository import InstalmentRepository
from repositories.collection_repository import CollectionRepository
from services.collection_service import CollectionService
from template_engine import template_engine

@router.get('/app')
@router.get('/app/dashboard')
def app_dashboard(req: Request) -> Response:
    auth_check = require_app_auth(req)
    if auth_check:
        return auth_check

    html_content = template_engine.render_file('app/dashboard.html', {'appuser': req.appuser})
    return Response.html(html_content)

@router.get('/app/collection/add')
def app_collection_add_get(req: Request) -> Response:
    auth_check = require_app_auth(req)
    if auth_check:
        return auth_check

    loans = LoanRepository.get_dropdown_list()
    context = {
        'appuser': req.appuser,
        'loan_list': loans,
        'msg': req.get_flash('msg'),
        'errors': {}
    }
    html_content = template_engine.render_file('app/collection.html', context)
    return Response.html(html_content)

@router.post('/app/collection/add')
def app_collection_add_post(req: Request) -> Response:
    auth_check = require_app_auth(req)
    if auth_check:
        return auth_check

    loan_id_str = req.form_data.get('loan_id', '').strip()
    inst_amt_str = req.form_data.get('instalment_amt', '').strip()
    payment_date = req.form_data.get('payment_date', '').strip()
    remark = req.form_data.get('remark', '').strip()

    errors = {}
    if not loan_id_str:
        errors['loan_id'] = 'Client Name/ Application No. is required.'
    if not inst_amt_str:
        errors['instalment_amt'] = 'Instalment Amount is required.'
    if not payment_date:
        errors['payment_date'] = 'Date is required.'

    if errors:
        loans = LoanRepository.get_dropdown_list()
        context = {
            'appuser': req.appuser,
            'loan_list': loans,
            'msg': '',
            'errors': errors
        }
        return Response.html(template_engine.render_file('app/collection.html', context))

    try:
        loan_id = int(loan_id_str)
        inst_amt = Decimal(inst_amt_str)
        success, msg, _ = CollectionService.add_collection(loan_id, inst_amt, payment_date, remark)
        alert_class = "alert-success" if success else "alert-danger"
        req.set_flash('msg', f'<div class="alert {alert_class} alert-dismissible"><a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a>{msg}</div>')
    except Exception as e:
        req.set_flash('msg', f'<div class="alert alert-danger">Error: {e}</div>')

    return Response.redirect('/app/collection/add')

@router.post('/app/collection/getInstalmentAmount')
def app_get_instalment_amount(req: Request) -> Response:
    loan_id = req.form_data.get('loan_id') or (req.json_data.get('loan_id') if req.json_data else None)
    if not loan_id:
        return Response.json({'status': 400, 'error': 'Missing loan_id'})

    loan = LoanRepository.get_by_id(int(loan_id))
    if not loan:
        return Response.json({'status': 404, 'error': 'Loan not found'})

    return Response.json({
        'status': 200,
        'data': {
            'instalment_amount': float(loan['instalment_amount']),
            'due_amount': float(loan['due_amount'])
        }
    })

@router.get('/app/collection/list')
def app_collection_list(req: Request) -> Response:
    auth_check = require_app_auth(req)
    if auth_check:
        return auth_check

    collections = CollectionRepository.get_all()
    context = {
        'appuser': req.appuser,
        'collection_list': collections,
        'msg': req.get_flash('msg')
    }
    html_content = template_engine.render_file('app/collection-list.html', context)
    return Response.html(html_content)

@router.get('/app/collection/todayCollection')
def app_today_collection(req: Request) -> Response:
    auth_check = require_app_auth(req)
    if auth_check:
        return auth_check

    today_str = date.today().strftime('%Y-%m-%d')
    collections = CollectionRepository.get_by_date(today_str)
    context = {
        'appuser': req.appuser,
        'collection_list': collections,
        'msg': req.get_flash('msg')
    }
    html_content = template_engine.render_file('app/todaycollection-list.html', context)
    return Response.html(html_content)

@router.get('/app/collection/todayPending')
def app_today_pending(req: Request) -> Response:
    auth_check = require_app_auth(req)
    if auth_check:
        return auth_check

    today_str = date.today().strftime('%Y-%m-%d')
    pending = InstalmentRepository.get_pending_by_date(today_str)
    context = {
        'appuser': req.appuser,
        'collection_list': pending,
        'msg': req.get_flash('msg')
    }
    html_content = template_engine.render_file('app/today-pending-collection.html', context)
    return Response.html(html_content)

@router.get('/app/collection/instalment/{loan_id}')
def app_instalment_view(req: Request, loan_id: str) -> Response:
    auth_check = require_app_auth(req)
    if auth_check:
        return auth_check

    lid = int(loan_id)
    loan = LoanRepository.get_by_id(lid)
    if not loan:
        return Response.redirect('/app/collection/list')

    instalments = InstalmentRepository.get_by_loan_id(lid)
    collections = CollectionRepository.get_by_loan_id(lid)
    coll_map = {c['instal_no']: c for c in collections}

    cumulative_paid = 0.0
    loan_interest = float(loan['loan_intrest_amount'])
    rows = []
    for inst in instalments:
        row = dict(inst)
        if inst['status'] == 'paid':
            cumulative_paid += float(inst['instalment_amt'])
            row['debit'] = float(inst['instalment_amt'])
            row['balance'] = max(0.0, loan_interest - cumulative_paid)
            c_info = coll_map.get(inst['instalment_no'])
            row['deposit_date'] = c_info['collect_date'] if c_info else inst.get('collect_date')
            row['remark'] = c_info['remark'] if c_info else ''
        else:
            row['debit'] = None
            row['balance'] = None
            row['deposit_date'] = None
            row['remark'] = None
        rows.append(row)

    context = {
        'appuser': req.appuser,
        'loan': loan,
        'instalment': rows,
        'forInstalment': collections
    }
    html_content = template_engine.render_file('app/collect-instalment-list.html', context)
    return Response.html(html_content)

@router.get('/app/collection/print/{collection_id}')
def app_print_receipt(req: Request, collection_id: str) -> Response:
    receipt = CollectionService.get_receipt(int(collection_id))
    if not receipt:
        return Response("Receipt not found", status=404)

    html_content = template_engine.render_file('app/receipt-print.html', {'receipt': receipt})
    return Response.html(html_content)
