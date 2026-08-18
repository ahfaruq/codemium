#!/usr/bin/env python3
from __future__ import annotations

import ast
import importlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

PARSER_VERSION = "3"

SYMBOL_PATTERNS = [
    ("FUNCTION", re.compile(r"^\s*(?:async\s+)?def\s+([A-Za-z_]\w*)", re.M)),
    ("CLASS", re.compile(r"^\s*class\s+([A-Za-z_]\w*)", re.M)),
    ("FUNCTION", re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)", re.M)),
    ("FUNCTION", re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>", re.M)),
    ("FUNCTION", re.compile(r"^\s*func\s+(?:\([^)]*\)\s*)?([A-Za-z_]\w*)", re.M)),
    ("FUNCTION", re.compile(r"^\s*(?:pub\s+)?fn\s+([A-Za-z_]\w*)", re.M)),
    ("CLASS", re.compile(r"^\s*(?:pub\s+)?(?:struct|enum|trait)\s+([A-Za-z_]\w*)", re.M)),
    ("CLASS", re.compile(r"^\s*(?:public\s+|private\s+|protected\s+)?(?:class|interface|record)\s+([A-Za-z_]\w*)", re.M)),
]
IMPORT_PATTERNS = [
    re.compile(r"(?:from|import)\s+[\"']([^\"']+)[\"']"),
    re.compile(r"require\([\"']([^\"']+)[\"']\)"),
    re.compile(r"^\s*from\s+([\w.]+)\s+import", re.M),
    re.compile(r"^\s*import\s+([\w.]+)", re.M),
]
CALL_PATTERN = re.compile(r"(?<![\w$.])([A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*)\s*\(")
EXTENDS_PATTERN = re.compile(r"\bclass\s+([A-Za-z_$][\w$]*)\s+(extends|implements)\s+([A-Za-z_$][\w$]*)")
SKIP_CALL_NAMES = {"if", "for", "while", "switch", "catch", "return", "function", "def", "class", "typeof", "sizeof", "new"}


def _module_id(path: str) -> str:
    return f"module:{path}"


def _symbol_id(path: str, qualified: str, kind: str) -> str:
    return f"symbol:{path}#{qualified}:{kind.lower()}"


def _empty_facts() -> dict:
    return {"symbols": [], "imports": [], "calls": [], "inherits": [], "references": [], "exports": []}


@dataclass(frozen=True)
class ParseResult:
    facts: dict
    parser: str
    capabilities: list[str]
    metadata: dict


class ParserAdapter(Protocol):
    name: str

    def supports(self, path: str, language: str) -> bool: ...
    def available(self) -> bool: ...
    def parse(self, path: str, language: str, text: str) -> ParseResult: ...


def dotted_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        left = dotted_name(node.value)
        return f"{left}.{node.attr}" if left else node.attr
    return None


class PythonExtractor(ast.NodeVisitor):
    def __init__(self, path: str):
        self.path = path
        self.stack: list[tuple[str, str]] = []
        self.facts = _empty_facts()

    def _qualify(self, name: str) -> str:
        parents = [x[0] for x in self.stack]
        return ".".join([*parents, name]) if parents else name

    def _owner(self) -> str | None:
        if not self.stack:
            return None
        name, kind = self.stack[-1]
        return _symbol_id(self.path, name, kind)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.facts["imports"].append({"module": alias.name, "imported": None, "alias": alias.asname or alias.name.split(".")[0], "line": node.lineno, "provenance": "DIRECT"})

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = ("." * node.level) + (node.module or "")
        for alias in node.names:
            self.facts["imports"].append({"module": module, "imported": alias.name, "alias": alias.asname or alias.name, "line": node.lineno, "provenance": "DIRECT"})

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        q = self._qualify(node.name)
        self.facts["symbols"].append({"name": node.name, "qualified_name": q, "kind": "CLASS", "line_start": node.lineno, "line_end": getattr(node, "end_lineno", node.lineno)})
        for base in node.bases:
            name = dotted_name(base)
            if name:
                self.facts["inherits"].append({"source": _symbol_id(self.path, q, "CLASS"), "target_name": name, "relation": "INHERITS", "line": node.lineno, "provenance": "DIRECT"})
        self.stack.append((q, "CLASS")); self.generic_visit(node); self.stack.pop()

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        kind = "METHOD" if self.stack and self.stack[-1][1] == "CLASS" else "FUNCTION"
        q = self._qualify(node.name)
        self.facts["symbols"].append({"name": node.name, "qualified_name": q, "kind": kind, "line_start": node.lineno, "line_end": getattr(node, "end_lineno", node.lineno)})
        self.stack.append((q, kind)); self.generic_visit(node); self.stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None: self._visit_function(node)
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None: self._visit_function(node)

    def visit_Call(self, node: ast.Call) -> None:
        name = dotted_name(node.func)
        if name:
            self.facts["calls"].append({"source": self._owner() or _module_id(self.path), "target_name": name, "line": getattr(node, "lineno", None), "provenance": "DIRECT"})
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load) and self._owner():
            self.facts["references"].append({"source": self._owner(), "target_name": node.id, "line": getattr(node, "lineno", None), "provenance": "DIRECT"})


class PythonAstParser:
    name = "python-ast"
    def supports(self, path: str, language: str) -> bool: return language == "python"
    def available(self) -> bool: return True
    def parse(self, path: str, language: str, text: str) -> ParseResult:
        tree = ast.parse(text)
        ex = PythonExtractor(path); ex.visit(tree)
        return ParseResult(ex.facts, self.name, ["symbols", "imports", "calls", "references", "inherits"], {"deep": True, "language": language})


def _text(source: bytes, node) -> str:
    return source[node.start_byte:node.end_byte].decode("utf-8", errors="ignore")


def _string_value(source: bytes, node) -> str:
    raw = _text(source, node).strip()
    if len(raw) >= 2 and raw[0] in "'\"`" and raw[-1] == raw[0]:
        return raw[1:-1]
    return raw


def _named_child(node, field: str):
    try:
        return node.child_by_field_name(field)
    except Exception:
        return None


def _walk(node):
    yield node
    for child in node.children:
        yield from _walk(child)


def _identifier_text(source: bytes, node) -> str | None:
    if node is None: return None
    if node.type in {"identifier", "property_identifier", "type_identifier", "shorthand_property_identifier", "private_property_identifier"}:
        return _text(source, node)
    if node.type in {"member_expression", "subscript_expression", "nested_identifier", "qualified_type_identifier"}:
        raw = _text(source, node)
        return re.sub(r"\s+", "", raw)
    return _text(source, node).strip() or None


class TreeSitterJSTSParser:
    name = "tree-sitter"
    LANGUAGES = {"javascript", "typescript"}

    def supports(self, path: str, language: str) -> bool:
        return language in self.LANGUAGES and Path(path).suffix.lower() in {".js", ".jsx", ".ts", ".tsx"}

    def available(self) -> bool:
        try:
            importlib.import_module("tree_sitter")
            importlib.import_module("tree_sitter_javascript")
            importlib.import_module("tree_sitter_typescript")
            return True
        except Exception:
            return False

    def _language(self, path: str, language: str):
        from tree_sitter import Language
        suffix = Path(path).suffix.lower()
        if language == "javascript":
            mod = importlib.import_module("tree_sitter_javascript")
            return Language(mod.language()), "javascript"
        mod = importlib.import_module("tree_sitter_typescript")
        fn = "language_tsx" if suffix == ".tsx" else "language_typescript"
        return Language(getattr(mod, fn)()), "tsx" if suffix == ".tsx" else "typescript"

    def _parse_import(self, source: bytes, node) -> list[dict]:
        src_node = _named_child(node, "source")
        if not src_node:
            strings = [x for x in _walk(node) if x.type == "string"]
            src_node = strings[-1] if strings else None
        module = _string_value(source, src_node) if src_node else ""
        if not module: return []
        line = node.start_point[0] + 1
        raw = _text(source, node)
        rows: list[dict] = []
        if node.type == "export_statement":
            return [{"module": module, "imported": None, "alias": None, "line": line, "provenance": "DIRECT", "reexport": True}]
        # Side-effect import.
        if " from " not in raw and raw.strip().startswith("import") and raw.count("'") + raw.count('"') >= 2:
            return [{"module": module, "imported": None, "alias": None, "line": line, "provenance": "DIRECT"}]
        clause = raw.split("from", 1)[0].replace("import", "", 1).strip()
        default_match = re.match(r"([A-Za-z_$][\w$]*)\s*(?:,|$)", clause)
        if default_match:
            rows.append({"module": module, "imported": "default", "alias": default_match.group(1), "line": line, "provenance": "DIRECT"})
        ns = re.search(r"\*\s+as\s+([A-Za-z_$][\w$]*)", clause)
        if ns:
            rows.append({"module": module, "imported": "*", "alias": ns.group(1), "line": line, "provenance": "DIRECT"})
        named = re.search(r"\{(.*?)\}", clause, re.S)
        if named:
            for part in named.group(1).split(","):
                part = part.strip()
                if not part: continue
                m = re.match(r"([A-Za-z_$][\w$]*)(?:\s+as\s+([A-Za-z_$][\w$]*))?", part)
                if m:
                    rows.append({"module": module, "imported": m.group(1), "alias": m.group(2) or m.group(1), "line": line, "provenance": "DIRECT"})
        return rows or [{"module": module, "imported": None, "alias": None, "line": line, "provenance": "DIRECT"}]

    def parse(self, path: str, language: str, text: str) -> ParseResult:
        from tree_sitter import Parser
        lang, dialect = self._language(path, language)
        parser = Parser(lang)
        source = text.encode("utf-8")
        tree = parser.parse(source)
        facts = _empty_facts()
        owner_stack: list[tuple[int, str]] = []
        symbol_nodes: dict[int, tuple[str, str]] = {}

        symbol_types = {
            "function_declaration": "FUNCTION", "generator_function_declaration": "FUNCTION",
            "class_declaration": "CLASS", "abstract_class_declaration": "CLASS",
            "interface_declaration": "INTERFACE", "type_alias_declaration": "TYPE",
            "enum_declaration": "ENUM", "method_definition": "METHOD", "method_signature": "METHOD",
        }

        # First pass: symbols/imports/exports. This gives stable owner ids before call extraction.
        for node in _walk(tree.root_node):
            if node.type in symbol_types:
                kind = symbol_types[node.type]
                name_node = _named_child(node, "name")
                name = _identifier_text(source, name_node)
                if not name: continue
                parent_names = []
                p = node.parent
                while p is not None:
                    if id(p) in symbol_nodes:
                        parent_names.append(symbol_nodes[id(p)][0])
                    p = p.parent
                qualified = ".".join([*reversed(parent_names), name]) if parent_names else name
                facts["symbols"].append({"name": name, "qualified_name": qualified, "kind": kind, "line_start": node.start_point[0] + 1, "line_end": node.end_point[0] + 1})
                symbol_nodes[id(node)] = (qualified, kind)
                header = _text(source, node)[: min(800, node.end_byte - node.start_byte)]
                if kind == "CLASS":
                    for rel, target in re.findall(r"\b(extends|implements)\s+([A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)?)", header):
                        facts["inherits"].append({"source": _symbol_id(path, qualified, kind), "target_name": target, "relation": "IMPLEMENTS" if rel == "implements" else "INHERITS", "line": node.start_point[0] + 1, "provenance": "DIRECT"})
            elif node.type == "variable_declarator":
                name_node = _named_child(node, "name")
                value_node = _named_child(node, "value")
                if name_node and value_node and value_node.type in {"arrow_function", "function_expression", "generator_function"}:
                    name = _identifier_text(source, name_node)
                    if name:
                        facts["symbols"].append({"name": name, "qualified_name": name, "kind": "FUNCTION", "line_start": node.start_point[0] + 1, "line_end": node.end_point[0] + 1})
                        symbol_nodes[id(node)] = (name, "FUNCTION")
            elif node.type in {"import_statement", "export_statement"}:
                facts["imports"].extend(self._parse_import(source, node))
                if node.type == "export_statement":
                    raw = _text(source, node)
                    default = bool(re.search(r"\bexport\s+default\b", raw))
                    value = _named_child(node, "value") or _named_child(node, "declaration")
                    names = []
                    if value is not None:
                        n = _named_child(value, "name") or value
                        name = _identifier_text(source, n)
                        if name and re.match(r"^[A-Za-z_$][\w$]*$", name): names.append(name)
                    for child in _walk(node):
                        if child.type in {"export_specifier"}:
                            raw_spec = _text(source, child)
                            m = re.match(r"\s*([A-Za-z_$][\w$]*)(?:\s+as\s+([A-Za-z_$][\w$]*))?", raw_spec)
                            if m: facts["exports"].append({"local": m.group(1), "exported": m.group(2) or m.group(1), "line": node.start_point[0] + 1, "provenance": "DIRECT"})
                    for name in names:
                        facts["exports"].append({"local": name, "exported": "default" if default else name, "line": node.start_point[0] + 1, "provenance": "DIRECT"})

        def owner_for(node) -> str:
            p = node.parent
            while p is not None:
                if id(p) in symbol_nodes:
                    q, kind = symbol_nodes[id(p)]
                    return _symbol_id(path, q, kind)
                p = p.parent
            return _module_id(path)

        for node in _walk(tree.root_node):
            if node.type in {"call_expression", "new_expression"}:
                fn = _named_child(node, "function") or _named_child(node, "constructor")
                if fn is None and node.children: fn = node.children[0]
                name = _identifier_text(source, fn)
                if name:
                    facts["calls"].append({"source": owner_for(node), "target_name": name, "line": node.start_point[0] + 1, "provenance": "DIRECT", "call_kind": "new" if node.type == "new_expression" else "call"})
            elif node.type == "variable_declarator":
                # CommonJS: const x = require('./x') / const {x} = require('./x')
                value = _named_child(node, "value")
                name_node = _named_child(node, "name")
                if value and value.type == "call_expression" and re.match(r"require\s*\(", _text(source, value)):
                    strings = [x for x in _walk(value) if x.type == "string"]
                    if strings:
                        module = _string_value(source, strings[0]); raw_name = _text(source, name_node) if name_node else ""
                        if raw_name.startswith("{"):
                            for part in raw_name.strip("{} ").split(","):
                                m = re.match(r"\s*([A-Za-z_$][\w$]*)(?:\s*:\s*([A-Za-z_$][\w$]*))?", part)
                                if m: facts["imports"].append({"module": module, "imported": m.group(1), "alias": m.group(2) or m.group(1), "line": node.start_point[0] + 1, "provenance": "DIRECT", "commonjs": True})
                        elif raw_name:
                            facts["imports"].append({"module": module, "imported": "*", "alias": raw_name.strip(), "line": node.start_point[0] + 1, "provenance": "DIRECT", "commonjs": True})

        # Deduplicate facts deterministically.
        for key in facts:
            unique = []
            seen = set()
            for row in facts[key]:
                marker = tuple(sorted((k, str(v)) for k, v in row.items()))
                if marker not in seen:
                    seen.add(marker); unique.append(row)
            facts[key] = unique
        caps = ["symbols", "imports", "calls", "inherits", "exports", "cross_language_bindings"]
        return ParseResult(facts, f"tree-sitter-{dialect}", caps, {"deep": True, "language": language, "dialect": dialect, "has_error": bool(tree.root_node.has_error)})


class RegexFallbackParser:
    name = "fallback-regex"
    def supports(self, path: str, language: str) -> bool: return True
    def available(self) -> bool: return True
    def parse(self, path: str, language: str, text: str) -> ParseResult:
        facts = _empty_facts(); seen = set()
        for kind, pat in SYMBOL_PATTERNS:
            for m in pat.finditer(text):
                name = m.group(1); key = (name, kind)
                if key in seen: continue
                seen.add(key); line = text.count("\n", 0, m.start()) + 1
                facts["symbols"].append({"name": name, "qualified_name": name, "kind": kind, "line_start": line, "line_end": line})
        for pat in IMPORT_PATTERNS:
            for m in pat.finditer(text):
                facts["imports"].append({"module": m.group(1), "imported": None, "alias": None, "line": text.count("\n", 0, m.start()) + 1, "provenance": "DIRECT"})
        for m in CALL_PATTERN.finditer(text):
            name = m.group(1)
            if name.lower() not in SKIP_CALL_NAMES:
                facts["calls"].append({"source": _module_id(path), "target_name": name, "line": text.count("\n", 0, m.start()) + 1, "provenance": "HEURISTIC"})
        for m in EXTENDS_PATTERN.finditer(text):
            child, keyword, parent = m.groups()
            src = next((_symbol_id(path, s["qualified_name"], s["kind"]) for s in facts["symbols"] if s["name"] == child), _module_id(path))
            facts["inherits"].append({"source": src, "target_name": parent, "relation": "IMPLEMENTS" if keyword == "implements" else "INHERITS", "line": text.count("\n", 0, m.start()) + 1, "provenance": "HEURISTIC"})
        return ParseResult(facts, self.name, ["symbols", "imports", "calls"], {"deep": False, "language": language})


PARSERS: list[ParserAdapter] = [PythonAstParser(), TreeSitterJSTSParser(), RegexFallbackParser()]


def parser_runtime() -> dict:
    ts = next(p for p in PARSERS if isinstance(p, TreeSitterJSTSParser))
    return {"parser_version": PARSER_VERSION, "tree_sitter_available": ts.available(), "deep_languages": ["python"] + (["javascript", "typescript", "tsx"] if ts.available() else [])}


def parse_source(path: str, language: str, text: str) -> ParseResult:
    last_error: Exception | None = None
    for parser in PARSERS:
        if not parser.supports(path, language) or not parser.available():
            continue
        try:
            return parser.parse(path, language, text)
        except (SyntaxError, ValueError, RuntimeError, ImportError, AttributeError) as exc:
            last_error = exc
            continue
    result = RegexFallbackParser().parse(path, language, text)
    if last_error:
        result.metadata["degraded_reason"] = type(last_error).__name__
    return result
