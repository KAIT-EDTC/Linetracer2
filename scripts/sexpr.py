"""Minimal S-expression reader/writer for KiCad files.

Atoms are kept as Python ``str``; quoted strings become ``Q`` (a str subclass)
so that they are written back with quotes.  Lists are Python lists.
"""
import re


class Q(str):
    """A quoted string atom."""


_TOKEN = re.compile(r'\s*(\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+)', re.S)


def parse(text):
    pos = 0
    stack = [[]]
    n = len(text)
    while pos < n:
        m = _TOKEN.match(text, pos)
        if not m:
            if text[pos:].strip() == "":
                break
            raise ValueError("parse error at %d: %r" % (pos, text[pos:pos + 40]))
        tok = m.group(1)
        pos = m.end()
        if tok == "(":
            stack.append([])
        elif tok == ")":
            node = stack.pop()
            stack[-1].append(node)
        elif tok.startswith('"'):
            body = tok[1:-1]
            body = body.replace('\\"', '"').replace("\\\\", "\\")
            stack[-1].append(Q(body))
        else:
            stack[-1].append(tok)
    assert len(stack) == 1, "unbalanced parens"
    return stack[0][0] if len(stack[0]) == 1 else stack[0]


def _fmt_atom(a):
    if isinstance(a, Q):
        return '"' + a.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if isinstance(a, float):
        s = ("%.4f" % a).rstrip("0").rstrip(".")
        return "0" if s in ("-0", "") else s
    if isinstance(a, bool):
        return "yes" if a else "no"
    return str(a)


def dump(node, indent=0):
    """Pretty print in a KiCad-like style (one list per line when nested)."""
    pad = "\t" * indent
    if not isinstance(node, list):
        return pad + _fmt_atom(node)
    simple = all(not isinstance(x, list) for x in node)
    if simple:
        return pad + "(" + " ".join(_fmt_atom(x) for x in node) + ")"
    # head atoms on the first line, nested lists on following lines
    head = []
    i = 0
    while i < len(node) and not isinstance(node[i], list):
        head.append(_fmt_atom(node[i]))
        i += 1
    lines = [pad + "(" + " ".join(head)]
    for x in node[i:]:
        lines.append(dump(x, indent + 1))
    lines.append(pad + ")")
    return "\n".join(lines)


def find(node, key):
    """First child list whose head == key."""
    for x in node:
        if isinstance(x, list) and x and x[0] == key:
            return x
    return None


def find_all(node, key):
    return [x for x in node if isinstance(x, list) and x and x[0] == key]


def get_prop(sym, name):
    for p in find_all(sym, "property"):
        if p[1] == name:
            return p
    return None
