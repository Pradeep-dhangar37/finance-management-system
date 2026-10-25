import unittest
from web import Router, Request, Response

class TestRouter(unittest.TestCase):
    """Unit tests for URL routing, path parameter extraction, and method isolation."""

    def setUp(self):
        self.router = Router()

    def test_exact_path_match(self):
        @self.router.get('/admin/login')
        def login_handler(req):
            return "login page"

        handler, params = self.router.match('GET', '/admin/login')
        self.assertIsNotNone(handler)
        self.assertEqual(params, {})
        self.assertEqual(handler(None), "login page")

    def test_parameter_extraction(self):
        @self.router.get('/admin/loan/edit/{loan_id}')
        def edit_loan_handler(req, loan_id):
            return f"editing loan {loan_id}"

        handler, params = self.router.match('GET', '/admin/loan/edit/42')
        self.assertIsNotNone(handler)
        self.assertEqual(params, {'loan_id': '42'})
        self.assertEqual(handler(None, **params), "editing loan 42")

    def test_multiple_parameters(self):
        @self.router.get('/report/{branch_id}/date/{report_date}')
        def branch_report(req, branch_id, report_date):
            return f"branch {branch_id} on {report_date}"

        handler, params = self.router.match('GET', '/report/5/date/2023-05-10')
        self.assertIsNotNone(handler)
        self.assertEqual(params, {'branch_id': '5', 'report_date': '2023-05-10'})

    def test_method_isolation(self):
        @self.router.get('/admin/branch')
        def get_branch(req):
            return "GET branch"

        @self.router.post('/admin/branch')
        def post_branch(req):
            return "POST branch"

        get_handler, _ = self.router.match('GET', '/admin/branch')
        post_handler, _ = self.router.match('POST', '/admin/branch')
        put_handler, _ = self.router.match('PUT', '/admin/branch')

        self.assertEqual(get_handler(None), "GET branch")
        self.assertEqual(post_handler(None), "POST branch")
        self.assertIsNone(put_handler)

    def test_unmatched_route_returns_none(self):
        handler, params = self.router.match('GET', '/non/existent/path')
        self.assertIsNone(handler)

if __name__ == '__main__':
    unittest.main()
