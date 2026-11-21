"""Inspect documentation and Python syntax without executing project code."""
import ast
import os
import re
from pathlib import Path
from .phrases import QRCODEGENERATION, NOQRCODEGENERATION, GENERIC_NAMES


def normalize(text):
    return ' '.join(text.lower().replace('’', "'").replace("n't", ' not').replace('-', ' ').split())


def pattern(phrases):
    return re.compile(r'\b(?:' + '|'.join(re.escape(p) for p in sorted(phrases, key=lambda p: (-len(p), p))) + r')\b')


def paragraphs(text):
    lines, fence = [], None
    for line in text.splitlines():
        mark = re.match(r'^ {0,3}(`{3,}|~{3,})', line)
        if fence:
            if re.match(r'^ {0,3}' + re.escape(fence[0]) + '{' + str(len(fence)) + r',}\s*$', line):
                fence = None
            lines.append('')
        elif mark:
            fence = mark.group(1)
            lines.append('')
        else:
            lines.append(line)
    return [normalize(p) for p in re.split(r'\n\s*\n', '\n'.join(lines)) if p.strip()]


def evidence(source):
    try:
        nodes = list(ast.walk(ast.parse(source)))
    except (SyntaxError, ValueError):
        return False
    imports, shadows, definitions = {}, set(), set()
    def names(target):
        if isinstance(target, ast.Name):
            return {target.id}
        if isinstance(target, (ast.Tuple, ast.List)):
            return set().union(*(names(x) for x in target.elts))
        if isinstance(target, ast.Starred):
            return names(target.value)
        return set()
    for node in nodes:
        if isinstance(node, ast.Import):
            for a in node.names:
                imports[a.asname or a.name.split('.')[0]] = a.name if a.asname else a.name.split('.')[0]
        elif isinstance(node, ast.ImportFrom) and not node.level:
            for a in node.names:
                imports[a.asname or a.name] = (node.module or '') + '.' + a.name
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            definitions.add(node.name)
            shadows.add(node.name)
        targets = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            targets = [x.optional_vars for x in node.items if x.optional_vars]
        for target in targets:
            shadows.update(names(target))
    constructor = method = False
    for node in nodes:
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        resolved = ''
        if isinstance(func, ast.Name):
            if func.id not in shadows:
                resolved = imports.get(func.id, '')
            name = resolved.rsplit('.', 1)[-1]
        elif isinstance(func, ast.Attribute):
            name = func.attr
            base = func.value
            while isinstance(base, ast.Attribute):
                base = base.value
            if isinstance(base, ast.Name):
                if base.id in imports and base.id in shadows:
                    continue
                resolved = imports.get(base.id, '')
        else:
            continue
        if name in definitions:
            continue
        attr = isinstance(func, ast.Attribute)
        if name in GENERIC_NAMES and (attr or resolved):
            return True
        def library(lib, member):
            return ((attr and name == member and (resolved == lib or resolved.startswith(lib + '.'))) or
                    (not attr and resolved == lib + '.' + member))
        if library('qrcode', 'make') or library('pyqrcode', 'create'):
            return True
        if any(library('segno', member) for member in ('make', 'make_qr', 'make_micro', 'make_sequence')):
            return True
        constructor |= library('qrcode', 'QRCode')
        method |= attr and name in ('make', 'make_image')
        if attr and name in ('encode_text', 'encode_binary', 'encode_segments'):
            value = func.value
            if isinstance(value, ast.Name) and imports.get(value.id) == 'qrcodegen.QrCode' and value.id not in shadows and 'QrCode' not in definitions:
                return True
            if isinstance(value, ast.Attribute) and value.attr == 'QrCode' and (resolved == 'qrcodegen' or resolved.startswith('qrcodegen.')) and 'QrCode' not in definitions:
                return True
    return bool(constructor and method)



def audit(root, ignore=(), fail_on='high'):
    root = Path(root)
    if not root.is_dir() or not os.access(str(root), os.R_OK | os.X_OK):
        raise OSError('Not a readable directory: {}'.format(root))
    claims = denials = production = tests = False
    yes_re, no_re = pattern(QRCODEGENERATION), pattern(NOQRCODEGENERATION)
    for directory, dirs, files in os.walk(str(root), followlinks=False, onerror=lambda e: (_ for _ in ()).throw(e)):
        parent = Path(directory)
        def ignored(path):
            rel = path.relative_to(root).as_posix()
            return any(rel == p.rstrip('/') or rel.startswith(p.rstrip('/') + '/') for p in ignore)
        dirs[:] = sorted(d for d in dirs if not (parent / d).is_symlink() and not ignored(parent / d))
        for filename in sorted(files):
            path = parent / filename
            if path.is_symlink() or ignored(path):
                continue
            rel = path.relative_to(root)
            if (rel.as_posix() == 'README.md' or ('docs' in rel.parts and path.suffix == '.md')):
                for para in paragraphs(path.read_text(encoding='utf-8')):
                    denials |= bool(no_re.search(para))
                    claims |= bool(yes_re.search(no_re.sub(' ', para)))
            if path.suffix == '.py' and not any(x in rel.parts for x in ('fixtures', 'docs', 'examples')):
                is_test = 'tests' in rel.parts or filename.startswith('test_') or filename.endswith('_test.py')
                if evidence(path.read_text(encoding='utf-8')):
                    if is_test:
                        tests = True
                    else:
                        production = True
    findings = []
    if claims and not production:
        severity = 'MEDIUM' if tests else 'HIGH'
        findings.append({'rule': 'documented-qr-code-generation-claim-false', 'severity': severity, 'message': 'Documented claim has ' + ('test-only evidence.' if tests else 'no production evidence.')})
    if denials and production:
        findings.append({'rule': 'documented-no-qr-code-generation-claim-false', 'severity': 'HIGH', 'message': 'Documented denial conflicts with production evidence.'})
    fail = any(f['severity'] == 'HIGH' or fail_on.lower() == 'medium' for f in findings)
    return {'verdict': 'FAIL' if fail else 'PASS', 'findings': findings}
