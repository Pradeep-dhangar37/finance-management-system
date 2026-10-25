"""
Lightweight, robust template engine built with pure Python standard library.
Supports:
  - {{ variable }} and {{ object.attr }} or {{ dict.key }}
  - Filters: {{ val|safe }}, {{ val|date_format }}, {{ val|number_format }}
  - Conditionals: {% if expr %} ... {% elif expr %} ... {% else %} ... {% endif %}
  - Loops: {% for item in iterable %} ... {% endfor %} (with loop.index, loop.first, loop.last)
  - Partials: {% include 'path/to/template.html' %}
"""
import re
import html
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional
from config import Config

def format_date(val: Any, fmt: str = '%d-%m-%Y') -> str:
    """Format dates to dd-mm-yyyy or specified format."""
    if not val:
        return ""
    if isinstance(val, (datetime, date)):
        return val.strftime(fmt)
    s = str(val).strip()
    for infmt in ('%Y-%m-%d', '%d-%m-%Y', '%Y-%m-%d %H:%M:%S', '%d-%m-%Y %H:%M'):
        try:
            return datetime.strptime(s, infmt).strftime(fmt)
        except ValueError:
            pass
    return s

def format_number(val: Any, decimals: int = 2) -> str:
    """Format numerical values with fixed decimals."""
    if val is None or val == '':
        return "0.00"
    try:
        f = float(val)
        return f"{f:.{decimals}f}"
    except (ValueError, TypeError):
        return str(val)

FILTERS = {
    'safe': lambda v: str(v) if v is not None else '',
    'escape': lambda v: html.escape(str(v)) if v is not None else '',
    'date_format': format_date,
    'number_format': format_number,
    'upper': lambda v: str(v).upper() if v is not None else '',
    'lower': lambda v: str(v).lower() if v is not None else '',
}

class TemplateEngine:
    def __init__(self, templates_dir: Optional[Path] = None):
        self.templates_dir = templates_dir or Config.TEMPLATES_DIR

    def render_file(self, template_name: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Read and render a template file from templates directory."""
        file_path = self.templates_dir / template_name
        if not file_path.exists():
            raise FileNotFoundError(f"Template '{template_name}' not found at {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            template_str = f.read()
        return self.render_string(template_str, context or {})

    def render_string(self, template_str: str, context: Dict[str, Any]) -> str:
        """Render template string with context."""
        # 1. Resolve {% include '...' %} recursively
        def include_sub(match):
            inc_file = match.group(1).strip().strip("'\"")
            inc_path = self.templates_dir / inc_file
            if not inc_path.exists():
                return f"<!-- Include missing: {inc_file} -->"
            with open(inc_path, 'r', encoding='utf-8') as inc_f:
                return inc_f.read()

        # Handle includes (up to 5 levels deep)
        for _ in range(5):
            if '{% include' not in template_str:
                break
            template_str = re.sub(r"\{%\s*include\s+(['\"][^'\"]+['\"])\s*%\}", include_sub, template_str)

        # 2. Tokenize and parse block structures (for, if)
        tokens = re.split(r"(\{%.*?%\}|\{\{.*?\}\})", template_str, flags=re.DOTALL)
        result, _ = self._eval_tokens(tokens, 0, context)
        return result

    def _eval_tokens(self, tokens: List[str], idx: int, context: Dict[str, Any], stop_tags: Optional[List[str]] = None) -> tuple[str, int]:
        out = []
        stop_tags = stop_tags or []
        n = len(tokens)

        while idx < n:
            token = tokens[idx]
            idx += 1

            if not token:
                continue

            # Variable tag: {{ expression }}
            if token.startswith("{{") and token.endswith("}}"):
                expr = token[2:-2].strip()
                val = self._eval_variable(expr, context)
                out.append(str(val))

            # Block tag: {% ... %}
            elif token.startswith("{%") and token.endswith("%}"):
                tag_content = token[2:-2].strip()
                parts = tag_content.split()
                tag_name = parts[0] if parts else ""

                if tag_name in stop_tags:
                    # Return to caller with current index
                    return "".join(out), idx - 1

                if tag_name == "for":
                    # {% for item in iterable %}
                    var_name = parts[1]
                    # parts[2] is 'in'
                    iter_expr = parts[3]
                    iterable = self._resolve_expr(iter_expr, context) or []
                    if isinstance(iterable, dict):
                        items = list(iterable.items())
                    elif isinstance(iterable, (list, tuple)):
                        items = list(iterable)
                    else:
                        items = []

                    # Read inner block up to {% endfor %}
                    inner_tokens = []
                    depth = 1
                    while idx < n:
                        t = tokens[idx]
                        idx += 1
                        if t.startswith("{%") and t.endswith("%}"):
                            content = t[2:-2].strip().split()
                            if content and content[0] == "for":
                                depth += 1
                            elif content and content[0] == "endfor":
                                depth -= 1
                                if depth == 0:
                                    break
                        inner_tokens.append(t)

                    total_items = len(items)
                    for loop_i, item_val in enumerate(items, 1):
                        loop_ctx = context.copy()
                        loop_ctx[var_name] = item_val
                        loop_ctx['loop'] = {
                            'index': loop_i,
                            'first': loop_i == 1,
                            'last': loop_i == total_items,
                            'total': total_items
                        }
                        rendered_loop, _ = self._eval_tokens(inner_tokens, 0, loop_ctx)
                        out.append(rendered_loop)

                elif tag_name == "if":
                    # Parse full if / elif / else / endif structure
                    condition_expr = " ".join(parts[1:])
                    branches = [(condition_expr, [])]
                    depth = 1

                    while idx < n:
                        t = tokens[idx]
                        idx += 1
                        if t.startswith("{%") and t.endswith("%}"):
                            content = t[2:-2].strip().split()
                            if content and content[0] == "if":
                                depth += 1
                                branches[-1][1].append(t)
                            elif content and content[0] == "endif":
                                depth -= 1
                                if depth == 0:
                                    break
                                branches[-1][1].append(t)
                            elif depth == 1 and content and content[0] == "elif":
                                elif_cond = " ".join(content[1:])
                                branches.append((elif_cond, []))
                            elif depth == 1 and content and content[0] == "else":
                                branches.append(("True", []))
                            else:
                                branches[-1][1].append(t)
                        else:
                            branches[-1][1].append(t)

                    # Evaluate branches in order
                    branch_taken = False
                    for cond, branch_tokens in branches:
                        if self._eval_condition(cond, context):
                            rendered_branch, _ = self._eval_tokens(branch_tokens, 0, context)
                            out.append(rendered_branch)
                            branch_taken = True
                            break

            else:
                out.append(token)

        return "".join(out), idx

    def _resolve_expr(self, expr: str, context: Dict[str, Any]) -> Any:
        expr = expr.strip()
        if expr == 'True':
            return True
        if expr == 'False':
            return False
        if expr == 'None':
            return None
        if expr.startswith(('"', "'")) and expr.endswith(('"', "'")):
            return expr[1:-1]
        if expr.isdigit():
            return int(expr)
        try:
            return float(expr)
        except ValueError:
            pass

        # Lookup in context (e.g., 'user.username' or 'loan.loan_amount')
        parts = expr.split('.')
        val = context.get(parts[0])
        for p in parts[1:]:
            if val is None:
                break
            if isinstance(val, dict):
                val = val.get(p)
            elif hasattr(val, p):
                val = getattr(val, p)
            else:
                val = None
        return val

    def _eval_variable(self, expr: str, context: Dict[str, Any]) -> str:
        filter_parts = expr.split('|')
        var_expr = filter_parts[0].strip()
        val = self._resolve_expr(var_expr, context)

        # Apply filters
        auto_escape = True
        for f in filter_parts[1:]:
            f = f.strip()
            if f == 'safe':
                auto_escape = False
                continue
            if f in FILTERS:
                val = FILTERS[f](val)

        if val is None:
            return ""
        val_str = str(val)
        if auto_escape:
            return html.escape(val_str)
        return val_str

    def _eval_condition(self, cond: str, context: Dict[str, Any]) -> bool:
        cond = cond.strip()
        if not cond:
            return False

        # Support 'not' prefix
        if cond.startswith('not '):
            return not self._eval_condition(cond[4:], context)

        # Support binary operators
        for op in ('==', '!=', '>=', '<=', '>', '<', ' in ', ' not in '):
            if op in cond:
                left, right = cond.split(op, 1)
                lval = self._resolve_expr(left, context)
                rval = self._resolve_expr(right, context)
                if op == '==':
                    return str(lval) == str(rval)
                elif op == '!=':
                    return str(lval) != str(rval)
                elif op == '>=':
                    return float(lval or 0) >= float(rval or 0)
                elif op == '<=':
                    return float(lval or 0) <= float(rval or 0)
                elif op == '>':
                    return float(lval or 0) > float(rval or 0)
                elif op == '<':
                    return float(lval or 0) < float(rval or 0)
                elif op == ' in ':
                    return lval in (rval or [])
                elif op == ' not in ':
                    return lval not in (rval or [])

        # Single truthiness evaluation
        val = self._resolve_expr(cond, context)
        return bool(val)

template_engine = TemplateEngine()
