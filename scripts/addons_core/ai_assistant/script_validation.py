# SPDX-FileCopyrightText: 2025 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
AI Assistant - Script Validation Module

Validates generated Python scripts for safety before execution.
Blocks scripts containing unsafe operations like file deletion, network calls, or system commands.
"""

import ast
import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ValidationResult:
    """Result of script validation."""
    is_valid: bool
    errors: List[str]

    def __init__(self, is_valid: bool, errors: Optional[List[str]] = None):
        self.is_valid = is_valid
        self.errors = errors or []


# Unsafe modules that should not be imported
UNSAFE_MODULES = {
    # System execution
    'os', 'subprocess', 'sys', 'platform', 'shlex', 'pty', 'grp', 'pwd',
    'spwd', 'msvcrt', 'winreg', 'winsound', '_winapi', 'win32api', 'win32con',
    'ctypes', '_ctypes', 'ctypes.wintypes',
    # Network operations
    'socket', 'urllib', 'urllib.request', 'urllib.parse', 'http', 'http.client',
    'http.server', 'ftplib', 'poplib', 'imaplib', 'nntplib', 'smtplib',
    'aiohttp', 'requests', 'urllib3', 'socketserver', 'xmlrpc', 'xmlrpc.client',
    # File system dangerous operations
    'shutil', 'pathlib', 'tempfile', 'fileinput', 'linecache',
    # Security/cryptographic
    'hmac', 'secrets', 'ssl', 'hashlib',
    # Other dangerous modules
    'multiprocessing', 'threading', 'asyncio.subprocess', 'concurrent.futures.process',
    'webbrowser', 'idlelib', 'pdb', 'code', 'codeop', 'compileall', 'py_compile',
}

# Unsafe attributes/methods on allowed modules (e.g., bpy)
UNSAFE_ATTRIBUTES = {
    # File operations
    'rmtree', 'remove', 'unlink', 'delete', 'removedirs', 'rmdir',
    # System calls
    'system', 'popen', 'popen2', 'popen3', 'popen4', 'call', 'check_call',
    'check_output', 'run', 'getoutput', 'getstatusoutput',
    # Network
    'urlopen', 'urlretrieve', 'URLopener', 'HTTPConnection', 'HTTPSConnection',
    'connect', 'bind', 'listen', 'accept', 'recv', 'send', 'sendall',
    # Process
    'fork', 'kill', 'killpg', 'abort', 'exit', 'Process', 'Pool',
    # Import related
    '__import__', 'reload', 'importlib', 'imp',
}

# Pattern-based detection for dynamic code execution
DANGEROUS_PATTERNS = [
    # Dynamic code execution
    (r'\beval\s*\(', 'eval() is not allowed'),
    (r'\bexec\s*\(', 'exec() is not allowed'),
    (r'\bexec\s+["\'\[]', 'exec statement is not allowed'),
    (r'\bcompile\s*\(', 'compile() is not allowed'),
    (r'__import__\s*\(', '__import__() is not allowed'),
    (r'\bgetattr\s*\([^)]*__', 'Accessing dunder attributes is not allowed'),
    (r'\bsetattr\s*\([^)]*__', 'Setting dunder attributes is not allowed'),
    # File deletion patterns
    (r'\bopen\s*\([^)]*[\'"]w', 'File write mode may be unsafe - use bpy specific file operations'),
    (r'os\.path\.exists.*remove', 'File deletion detected'),
    (r'os\.remove', 'os.remove() is not allowed'),
    (r'os\.unlink', 'os.unlink() is not allowed'),
    (r'shutil\.rmtree', 'shutil.rmtree() is not allowed'),
    # Network patterns
    (r'http[s]?://', 'Network URLs are not allowed'),
    (r'socket\.', 'socket operations are not allowed'),
    # System command patterns
    (r'[`]\s*[^`]+[`]', 'Backtick shell execution is not allowed'),
    (r'\$\([^)]+\)', 'Command substitution is not allowed'),
    # Environment access
    (r'os\.environ', 'Accessing environment variables is not allowed'),
    (r'sys\.exit', 'sys.exit() is not allowed'),
    # Private attribute access
    (r'\b_[a-zA-Z_][a-zA-Z0-9_]*__[a-zA-Z_]', 'Name mangled private attributes are not allowed'),
]


class ScriptValidator(ast.NodeVisitor):
    """AST visitor to check for unsafe code patterns."""

    def __init__(self):
        self.errors: List[str] = []
        self.imported_names: dict = {}  # Track what each name refers to

    def add_error(self, message: str, node: ast.AST):
        """Add an error with line number."""
        self.errors.append(f"Line {node.lineno}: {message}")

    def visit_Import(self, node: ast.Import):
        """Check for unsafe module imports."""
        for alias in node.names:
            module_name = alias.name.split('.')[0]
            if module_name in UNSAFE_MODULES:
                self.add_error(f"Import of unsafe module '{alias.name}' is not allowed", node)
            # Track the import for later name resolution
            name = alias.asname or alias.name
            self.imported_names[name] = alias.name
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Check for unsafe imports from modules."""
        if node.module:
            module_name = node.module.split('.')[0]
            if module_name in UNSAFE_MODULES:
                self.add_error(f"Import from unsafe module '{node.module}' is not allowed", node)
            # Check if importing specific unsafe functions
            for alias in node.names:
                full_name = f"{node.module}.{alias.name}" if node.module else alias.name
                base_module = full_name.split('.')[0] if full_name else ""
                if alias.name in UNSAFE_ATTRIBUTES:
                    self.add_error(f"Import of unsafe function '{alias.name}' from '{node.module}' is not allowed", node)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        """Check for dangerous function calls."""
        # Check for eval, exec, compile, etc.
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in ('eval', 'exec', 'compile'):
                self.add_error(f"Function '{func_name}()' is not allowed for security reasons", node)
            if func_name == '__import__':
                self.add_error("Dynamic imports with __import__() are not allowed", node)
            # Check if the function name is an unsafe module import
            if func_name in self.imported_names:
                original = self.imported_names[func_name]
                if original.split('.')[0] in UNSAFE_MODULES:
                    self.add_error(f"Call to unsafe module function is not allowed", node)

        # Check for method calls on unsafe modules or dangerous methods
        if isinstance(node.func, ast.Attribute):
            attr_name = node.func.attr
            if attr_name in UNSAFE_ATTRIBUTES:
                self.add_error(f"Call to unsafe method '{attr_name}()' is not allowed", node)

        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        """Check for access to unsafe attributes."""
        # Build the full attribute chain
        attr_chain = self._get_attr_chain(node)
        if attr_chain:
            # Check for unsafe module access
            first_part = attr_chain[0]
            if first_part in self.imported_names:
                first_part = self.imported_names[first_part]

            # Check for os.system, os.remove, etc.
            if len(attr_chain) >= 2:
                if attr_chain[0] == 'os' and attr_chain[1] in ('system', 'popen', 'remove', 'unlink', 'rmdir', 'removedirs', 'kill', 'fork', 'spawn'):
                    self.add_error(f"Access to 'os.{attr_chain[1]}' is not allowed", node)
                if attr_chain[0] == 'subprocess' and len(attr_chain) >= 2:
                    self.add_error(f"Access to subprocess functions is not allowed", node)
                if attr_chain[0] == 'sys' and attr_chain[1] in ('exit', 'exitfunc'):
                    self.add_error(f"Access to 'sys.{attr_chain[1]}' is not allowed", node)

        self.generic_visit(node)

    def _get_attr_chain(self, node: ast.AST) -> List[str]:
        """Extract the chain of attribute names from an AST node."""
        if isinstance(node, ast.Name):
            return [node.id]
        elif isinstance(node, ast.Attribute):
            base = self._get_attr_chain(node.value)
            if base:
                return base + [node.attr]
        return []

    def visit_Expr(self, node: ast.Expr):
        """Check expression statements."""
        # This catches exec statements (Python 2 style)
        if isinstance(node.value, ast.Call):
            call = node.value
            if isinstance(call.func, ast.Name) and call.func.id == 'exec':
                self.add_error("exec() is not allowed for security reasons", node)
        self.generic_visit(node)


def validate_script_syntax(script: str) -> ValidationResult:
    """Validate that a script has valid Python syntax."""
    try:
        ast.parse(script)
        return ValidationResult(True)
    except SyntaxError as e:
        return ValidationResult(False, [f"Syntax error at line {e.lineno}: {e.msg}"])
    except Exception as e:
        return ValidationResult(False, [f"Parse error: {str(e)}"])


def validate_script_safety(script: str) -> ValidationResult:
    """
    Validate a Python script for unsafe operations.

    Checks for:
    - Invalid syntax
    - Imports of unsafe modules
    - File deletion operations
    - Network operations
    - System command execution
    - Dynamic code execution (eval, exec, compile)

    Returns:
        ValidationResult with is_valid=True if script is safe, False otherwise
        with list of error messages if unsafe.
    """
    errors = []

    # First, check syntax
    syntax_result = validate_script_syntax(script)
    if not syntax_result.is_valid:
        return syntax_result

    # Pattern-based checks
    for pattern, message in DANGEROUS_PATTERNS:
        if re.search(pattern, script, re.IGNORECASE):
            errors.append(message)

    # AST-based analysis
    try:
        tree = ast.parse(script)
        validator = ScriptValidator()
        validator.visit(tree)
        errors.extend(validator.errors)
    except SyntaxError:
        # Already handled above
        pass
    except Exception as e:
        errors.append(f"AST analysis failed: {str(e)}")

    # Check for byte-compiled files or frozen modules
    if '__pycache__' in script:
        errors.append("References to __pycache__ are not allowed")
    if '.pyc' in script or '.pyo' in script:
        errors.append("Byte-compiled Python files are not allowed")

    # Check for import statements with suspicious patterns
    suspicious_imports = re.findall(r'^\s*(?:from|import)\s+(\S+)', script, re.MULTILINE)
    for imp in suspicious_imports:
        if imp.startswith('_'):
            errors.append(f"Import of private module '{imp}' is not allowed")

    if errors:
        return ValidationResult(False, errors)

    return ValidationResult(True)


def get_user_friendly_error_message(result: ValidationResult) -> str:
    """Convert validation errors into a user-friendly message."""
    if result.is_valid:
        return "Script validation passed"

    if not result.errors:
        return "Script validation failed for unknown reasons"

    # Format the errors nicely
    if len(result.errors) == 1:
        return f"Script validation failed: {result.errors[0]}"

    error_list = "\n".join(f"  - {e}" for e in result.errors[:5])  # Limit to first 5 errors
    if len(result.errors) > 5:
        error_list += f"\n  ... and {len(result.errors) - 5} more issues"

    return f"Script validation failed with {len(result.errors)} issues:\n{error_list}"
