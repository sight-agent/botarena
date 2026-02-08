from __future__ import annotations

import ast
import hashlib


def code_hash_py(code: str) -> str:
    """Return a stable hash for python code ignoring whitespace + comments.

    We parse into AST and hash the canonical ast.dump(). This ignores:
    - formatting/whitespace
    - comments

    It does NOT ignore:
    - identifier names
    - literal values
    - control flow

    Raises SyntaxError if code is invalid.
    """

    tree = ast.parse(code)
    canonical = ast.dump(tree, include_attributes=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
