"""Dashboard and due amount routes."""
from web import router, Request, Response
from routes.auth_routes import require_admin_auth
from services.dashboard_service import DashboardService
from repositories.loan_repository import LoanRepository
from template_engine import template_engine

@router.get('/')
@router.get('/admin')
def home_redirect(req: Request) -> Response:
    if req.user:
        return Response.redirect('/admin/dashboard')
    return Response.redirect('/admin/login')

@router.get('/admin/dashboard')
def admin_dashboard(req: Request) -> Response:
    auth_check = require_admin_auth(req)
    if auth_check:
        return auth_check

    metrics = DashboardService.get_metrics()
    context = {
        'user': req.user,
        **metrics
    }
    html_content = template_engine.render_file('admin/index.html', context)
    return Response.html(html_content)

@router.get('/admin/dashboard/totalDueAmount')
def total_due_amount(req: Request) -> Response:
    auth_check = require_admin_auth(req)
    if auth_check:
        return auth_check

    due_loans = LoanRepository.get_due_loans()
    total_due = sum(float(l['due_amount']) for l in due_loans) if due_loans else 0.0
    context = {
        'user': req.user,
        'loan_list': due_loans,
        'total_due': total_due,
        'msg': req.get_flash('msg')
    }
    html_content = template_engine.render_file('admin/total-due-list.html', context)
    return Response.html(html_content)
