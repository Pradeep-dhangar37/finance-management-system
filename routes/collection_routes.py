"""Collection management routes for installments, receipts, and listings."""
from datetime import date
from decimal import Decimal
from web import router, Request, Response
from routes.auth_routes import require_admin_auth
from repositories.loan_repository import LoanRepository
from repositories.instalment_repository import InstalmentRepository
from repositories.collection_repository import CollectionRepository
from services.collection_service import CollectionService
from template_engine import template_engine

@router.get('/admin/collection/add')
def collection_add_get(req: Request) -> Response:
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
    html_content = template_engine.render_file('admin/collection.html', context)
    return Response.html(html_content)

@router.post('/admin/collection/add')
def collection_add_post(req: Request) -> Response:
    auth_check = require_admin_auth(req)
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
            'user': req.user,
            'loan_list': loans,
            'msg': '',
            'errors': errors
        }
        return Response.html(template_engine.render_file('admin/collection.html', context))

    try:
        loan_id = int(loan_id_str)
        inst_amt = Decimal(inst_amt_str)
        success, msg, coll_id = CollectionService.add_collection(loan_id, inst_amt, payment_date, remark)
        alert_class = "alert-success" if success else "alert-danger"
        req.set_flash('msg', f'<div class="alert {alert_class} alert-dismissible"><a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a>{msg}</div>')
    except Exception as e:
        req.set_flash('msg', f'<div class="alert alert-danger">Error: {e}</div>')

    return Response.redirect('/admin/collection/add')

@router.post('/admin/collection/getInstalmentAmount')
def get_instalment_amount(req: Request) -> Response:
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

@router.get('/admin/collection/list')
def collection_list(req: Request) -> Response:
    auth_check = require_admin_auth(req)
    if auth_check:
        return auth_check

    collections = CollectionRepository.get_all()
    total_amount = 0.0

    # Annotate with whether this is the latest paid installment
    for c in collections:
        total_amount += float(c['instalment_amt'])
        latest_paid = InstalmentRepository.get_latest_paid(c['loan_id'])
        c['can_delete'] = (latest_paid and latest_paid['instalment_no'] == c['instal_no'])

    context = {
        'user': req.user,
        'collection_list': collections,
        'total_amount': total_amount,
        'msg': req.get_flash('msg')
    }
    html_content = template_engine.render_file('admin/collection-list.html', context)
    return Response.html(html_content)

@router.get('/admin/collection/todayCollection')
def today_collection(req: Request) -> Response:
    auth_check = require_admin_auth(req)
    if auth_check:
        return auth_check

    today_str = date.today().strftime('%Y-%m-%d')
    collections = CollectionRepository.get_by_date(today_str)
    total_amount = 0.0

    for c in collections:
        total_amount += float(c['instalment_amt'])
        latest_paid = InstalmentRepository.get_latest_paid(c['loan_id'])
        c['can_delete'] = (latest_paid and latest_paid['instalment_no'] == c['instal_no'])

    context = {
        'user': req.user,
        'collection_list': collections,
        'total_amount': total_amount,
        'msg': req.get_flash('msg')
    }
    html_content = template_engine.render_file('admin/todaycollection-list.html', context)
    return Response.html(html_content)

@router.get('/admin/collection/todayPending')
def today_pending_get(req: Request) -> Response:
    auth_check = require_admin_auth(req)
    if auth_check:
        return auth_check

    search_date = req.query_params.get('search_date') or date.today().strftime('%Y-%m-%d')
    pending = InstalmentRepository.get_pending_by_date(search_date)
    total_amount = sum(float(p['instalment_amt']) for p in pending) if pending else 0.0

    context = {
        'user': req.user,
        'collection_list': pending,
        'search_date': search_date,
        'total_amount': total_amount,
        'msg': req.get_flash('msg')
    }
    html_content = template_engine.render_file('admin/today-pending-collection.html', context)
    return Response.html(html_content)

@router.post('/admin/collection/todayPending')
def today_pending_post(req: Request) -> Response:
    auth_check = require_admin_auth(req)
    if auth_check:
        return auth_check

    search_date = req.form_data.get('search_date') or date.today().strftime('%Y-%m-%d')
    pending = InstalmentRepository.get_pending_by_date(search_date)
    total_amount = sum(float(p['instalment_amt']) for p in pending) if pending else 0.0

    context = {
        'user': req.user,
        'collection_list': pending,
        'search_date': search_date,
        'total_amount': total_amount,
        'msg': req.get_flash('msg')
    }
    html_content = template_engine.render_file('admin/today-pending-collection.html', context)
    return Response.html(html_content)

@router.get('/admin/collection/instalment/{loan_id}')
def collection_instalment_view(req: Request, loan_id: str) -> Response:
    auth_check = require_admin_auth(req)
    if auth_check:
        return auth_check

    lid = int(loan_id)
    loan = LoanRepository.get_by_id(lid)
    if not loan:
        return Response.redirect('/admin/collection/list')

    instalments = InstalmentRepository.get_by_loan_id(lid)
    collections = CollectionRepository.get_by_loan_id(lid)
    # Map collections by instal_no for quick lookup
    coll_map = {c['instal_no']: c for c in collections}

    # Prepare installment rows with balance calculations
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
        'user': req.user,
        'loan': loan,
        'instalment': rows,
        'forInstalment': collections
    }
    html_content = template_engine.render_file('admin/collect-instalment-list.html', context)
    return Response.html(html_content)

@router.post('/admin/collection/print')
def collection_print_post(req: Request) -> Response:
    coll_id_str = req.form_data.get('collection_id') or (req.json_data.get('collection_id') if req.json_data else None)
    if not coll_id_str:
        return Response("Missing collection_id", status=400)

    receipt = CollectionService.get_receipt(int(coll_id_str))
    if not receipt:
        return Response("Receipt not found", status=404)

    html_content = template_engine.render_file('admin/receipt-print.html', {'receipt': receipt})
    return Response.html(html_content)

@router.get('/admin/collection/print/{collection_id}')
def collection_print_get(req: Request, collection_id: str) -> Response:
    receipt = CollectionService.get_receipt(int(collection_id))
    if not receipt:
        return Response("Receipt not found", status=404)

    html_content = template_engine.render_file('admin/receipt-print.html', {'receipt': receipt})
    return Response.html(html_content)

@router.get('/admin/collection/deleteInstalment/{loan_id}/{instal_no}')
def collection_delete_instalment(req: Request, loan_id: str, instal_no: str) -> Response:
    auth_check = require_admin_auth(req)
    if auth_check:
        return auth_check

    lid = int(loan_id)
    ino = int(instal_no)
    success, msg = CollectionService.delete_instalment(lid, ino)
    alert_class = "alert-success" if success else "alert-danger"
    req.set_flash('msg', f'<div class="alert {alert_class} alert-dismissible"><a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a>{msg}</div>')
    return Response.redirect('/admin/collection/list')
