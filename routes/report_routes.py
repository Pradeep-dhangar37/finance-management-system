"""Financial reporting and ledger routes."""
from datetime import date
from decimal import Decimal
from web import router, Request, Response
from routes.auth_routes import require_admin_auth
from repositories.loan_repository import LoanRepository
from repositories.report_repository import ReportRepository
from services.ledger_service import LedgerService
from services.report_service import ReportService
from template_engine import template_engine

# ==================== LEDGER ====================

@router.get('/admin/ledger')
def ledger_get(req: Request) -> Response:
    auth_check = require_admin_auth(req)
    if auth_check:
        return auth_check

    loans = LoanRepository.get_dropdown_list()
    context = {
        'user': req.user,
        'loan_list': loans,
        'loan_id': '',
        'from_date': '',
        'to_date': '',
        'ledgerList': [],
        'collection': [],
        'initial_loan': None,
        'running_entries': [],
        'tot_instalment_amt': 0.0,
        'tot_balance': 0.0
    }
    return Response.html(template_engine.render_file('admin/ledger.html', context))

@router.post('/admin/ledger')
def ledger_post(req: Request) -> Response:
    auth_check = require_admin_auth(req)
    if auth_check:
        return auth_check

    loan_id_str = req.form_data.get('loan_id', '').strip()
    from_date = req.form_data.get('from_date', '').strip()
    to_date = req.form_data.get('to_date', '').strip()

    loans = LoanRepository.get_dropdown_list()
    if not loan_id_str:
        context = {
            'user': req.user,
            'loan_list': loans,
            'loan_id': '',
            'from_date': from_date,
            'to_date': to_date,
            'ledgerList': [],
            'collection': [],
            'initial_loan': None,
            'running_entries': [],
            'tot_instalment_amt': 0.0,
            'tot_balance': 0.0
        }
        return Response.html(template_engine.render_file('admin/ledger.html', context))

    lid = int(loan_id_str)
    ledger_data = LedgerService.get_ledger(lid, from_date, to_date)
    loan = ledger_data['loan']
    collections = ledger_data['collections']

    running_entries = []
    tot_instalment_amt = 0.0
    tot_balance = 0.0

    if loan:
        loan_interest = float(loan['loan_intrest_amount'])
        for idx, col in enumerate(collections, 1):
            tot_instalment_amt += float(col['instalment_amt'])
            bal = loan_interest - tot_instalment_amt
            running_entries.append({
                'payment_date': col['payment_date'],
                'instalment_no': idx,
                'instalment_amt': float(col['instalment_amt']),
                'balance': bal
            })
        tot_balance = loan_interest - tot_instalment_amt

    context = {
        'user': req.user,
        'loan_list': loans,
        'loan_id': lid,
        'from_date': from_date,
        'to_date': to_date,
        'ledgerList': [loan] if loan else [],
        'collection': collections,
        'initial_loan': loan,
        'running_entries': running_entries,
        'tot_instalment_amt': tot_instalment_amt,
        'tot_balance': tot_balance
    }
    return Response.html(template_engine.render_file('admin/ledger.html', context))

# ==================== REPORT 1: OUTSTANDING ====================

@router.get('/admin/report')
def report_outstanding_get(req: Request) -> Response:
    auth_check = require_admin_auth(req)
    if auth_check:
        return auth_check

    context = {
        'user': req.user,
        'to_date': '',
        'outstanding_list': [],
        'total_loan_amount': 0.0,
        'total_collective_amount': 0.0,
        'total_balance_amount': 0.0,
        'msg': req.get_flash('msg')
    }
    return Response.html(template_engine.render_file('admin/report.html', context))

@router.post('/admin/report')
def report_outstanding_post(req: Request) -> Response:
    auth_check = require_admin_auth(req)
    if auth_check:
        return auth_check

    to_date = req.form_data.get('to_date', '').strip()
    if not to_date:
        return Response.redirect('/admin/report')

    first_loan = ReportRepository.get_first_loan_date()
    if not first_loan:
        req.set_flash('msg', '<div class="alert alert-danger alert-dismissible"><a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a>No Record Available.</div>')
        return Response.redirect('/admin/report')

    outstanding = ReportService.get_outstanding_report(to_date)
    tot_loan = sum(float(l['loan_amount']) for l in outstanding)
    tot_coll = sum(float(l['loan_intrest_amount']) for l in outstanding)
    tot_bal = sum(float(l['balance_amount']) for l in outstanding)

    context = {
        'user': req.user,
        'to_date': to_date,
        'outstanding_list': outstanding,
        'total_loan_amount': tot_loan,
        'total_collective_amount': tot_coll,
        'total_balance_amount': tot_bal,
        'msg': req.get_flash('msg')
    }
    return Response.html(template_engine.render_file('admin/report.html', context))

# ==================== REPORT 2: OPENING/CLOSING BALANCE ====================

@router.get('/admin/report/opclosingbalReport')
def opclosing_report_get(req: Request) -> Response:
    auth_check = require_admin_auth(req)
    if auth_check:
        return auth_check

    records = ReportRepository.get_report_one_all()
    context = {
        'user': req.user,
        'rep_list': records,
        'msg': req.get_flash('msg'),
        'delmsg': req.get_flash('delmsg'),
        'errors': {}
    }
    return Response.html(template_engine.render_file('admin/opclosing-report.html', context))

@router.post('/admin/report/opclosingbalReport')
def opclosing_report_post(req: Request) -> Response:
    auth_check = require_admin_auth(req)
    if auth_check:
        return auth_check

    today_str = date.today().strftime('%Y-%m-%d')
    if ReportRepository.exists_report_one_date(today_str):
        req.set_flash('msg', '<div class="alert alert-danger alert-dismissible"><a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a>Record Already Added.</div>')
        return Response.redirect('/admin/report/opclosingbalReport')

    data = {
        'opening_bal': float(req.form_data.get('opening_bal', 0)),
        'total_collection': float(req.form_data.get('total_collection', 0)),
        'closing_bal': float(req.form_data.get('closing_bal', 0)),
        'rdpayment': float(req.form_data.get('rdpayment', 0)),
        'total_bal': float(req.form_data.get('total_bal', 0)),
        'ad_date': today_str
    }
    ReportRepository.add_report_one(data)
    req.set_flash('msg', '<div class="alert alert-success alert-dismissible"><a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a>Record Added Successfully.</div>')
    return Response.redirect('/admin/report/opclosingbalReport')

@router.get('/admin/report/opcloseDel/{id}')
def opclosing_report_delete(req: Request, id: str) -> Response:
    auth_check = require_admin_auth(req)
    if auth_check:
        return auth_check

    ReportRepository.delete_report_one(int(id))
    req.set_flash('delmsg', '<div class="alert alert-danger alert-dismissible"><a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a>Record Delete Successfully.</div>')
    return Response.redirect('/admin/report/opclosingbalReport')

# ==================== REPORT 3: TOTAL BALANCE / DISBURSEMENT ====================

@router.get('/admin/report/totalBalReport')
def totalbal_report_get(req: Request) -> Response:
    auth_check = require_admin_auth(req)
    if auth_check:
        return auth_check

    records = ReportRepository.get_report_two_all()
    context = {
        'user': req.user,
        'rep_list': records,
        'msg': req.get_flash('msg'),
        'delmsg': req.get_flash('delmsg'),
        'errors': {}
    }
    return Response.html(template_engine.render_file('admin/tot-bal-report.html', context))

@router.post('/admin/report/totalBalReport')
def totalbal_report_post(req: Request) -> Response:
    auth_check = require_admin_auth(req)
    if auth_check:
        return auth_check

    today_str = date.today().strftime('%Y-%m-%d')
    if ReportRepository.exists_report_two_date(today_str):
        req.set_flash('msg', '<div class="alert alert-danger alert-dismissible"><a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a>Record Already Added.</div>')
        return Response.redirect('/admin/report/totalBalReport')

    data = {
        'total_disabesment': float(req.form_data.get('total_disabesment', 0)),
        'current_outstanding': float(req.form_data.get('current_outstanding', 0)),
        'difference_outstanding': float(req.form_data.get('difference_outstanding', 0)),
        'client_disabsment': float(req.form_data.get('client_disabsment', 0)),
        'interest_amount': float(req.form_data.get('interest_amount', 0)),
        'ad_date': today_str
    }
    ReportRepository.add_report_two(data)
    req.set_flash('msg', '<div class="alert alert-success alert-dismissible"><a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a>Record Added Successfully.</div>')
    return Response.redirect('/admin/report/totalBalReport')

@router.get('/admin/report/totbalRepDel/{rid}')
def totalbal_report_delete(req: Request, rid: str) -> Response:
    auth_check = require_admin_auth(req)
    if auth_check:
        return auth_check

    ReportRepository.delete_report_two(int(rid))
    req.set_flash('delmsg', '<div class="alert alert-danger alert-dismissible"><a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a>Record Delete Successfully.</div>')
    return Response.redirect('/admin/report/totalBalReport')
