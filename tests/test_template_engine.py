import unittest
from template_engine import TemplateEngine

class TestTemplateEngine(unittest.TestCase):
    """Unit tests for the custom lightweight template engine."""

    def setUp(self):
        self.engine = TemplateEngine(templates_dir='templates')

    def test_variable_interpolation(self):
        tmpl = "Hello, {{ name }}! Balance: ₹{{ balance }}."
        result = self.engine.render_string(tmpl, {'name': 'Pradeep', 'balance': 5000})
        self.assertEqual(result, "Hello, Pradeep! Balance: ₹5000.")

    def test_for_loop(self):
        tmpl = "Users:{% for u in users %} {{ u.name }}{% endfor %}"
        context = {'users': [{'name': 'Alice'}, {'name': 'Bob'}]}
        result = self.engine.render_string(tmpl, context)
        self.assertEqual(result, "Users: Alice Bob")

    def test_if_condition_true(self):
        tmpl = "{% if is_admin %}Welcome Admin{% endif %}"
        result = self.engine.render_string(tmpl, {'is_admin': True})
        self.assertEqual(result, "Welcome Admin")

    def test_if_condition_false(self):
        tmpl = "{% if is_admin %}Welcome Admin{% endif %}"
        result = self.engine.render_string(tmpl, {'is_admin': False})
        self.assertEqual(result, "")

    def test_filter_date_format(self):
        tmpl = "Date: {{ my_date | date_format }}"
        result = self.engine.render_string(tmpl, {'my_date': '2023-11-25'})
        self.assertEqual(result, "Date: 25-11-2023")

    def test_filter_number_format(self):
        tmpl = "Amount: {{ amount | number_format }}"
        result = self.engine.render_string(tmpl, {'amount': 1234.5})
        self.assertEqual(result, "Amount: 1234.50")

if __name__ == '__main__':
    unittest.main()
