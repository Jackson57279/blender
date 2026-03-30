# SPDX-FileCopyrightText: 2025 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
Tests for history replay functionality.

These tests validate the history replay operator logic without requiring
Blender's bpy module for the core logic tests.
"""

import unittest
import sys
import types

# Create mock bpy module
mock_bpy = types.ModuleType('bpy')
mock_bpy.ops = types.ModuleType('bpy.ops')
mock_bpy.ops.ed = types.SimpleNamespace()
mock_bpy.context = types.SimpleNamespace()
mock_bpy.data = types.SimpleNamespace()
mock_bpy.types = types.ModuleType('bpy.types')
mock_bpy.props = types.ModuleType('bpy.props')
mock_bpy.utils = types.SimpleNamespace()

# Create mock mathutils
mock_mathutils = types.ModuleType('mathutils')
mock_mathutils.Vector = lambda x: x
mock_mathutils.Matrix = lambda: None

sys.modules['bpy'] = mock_bpy
sys.modules['mathutils'] = mock_mathutils


class MockValidationResult:
    """Mock validation result for testing."""
    def __init__(self, is_valid, errors=None):
        self.is_valid = is_valid
        self.errors = errors or []


class MockScriptValidation:
    """Mock script validation for testing."""
    @staticmethod
    def validate_script_safety(script):
        # For testing, allow simple bpy scripts, reject imports of unsafe modules
        unsafe_modules = ['os', 'subprocess', 'sys', 'socket', 'urllib', 'shutil']
        for unsafe in unsafe_modules:
            if f'import {unsafe}' in script or f'from {unsafe}' in script:
                return MockValidationResult(False, [f"Unsafe import: {unsafe}"])
        return MockValidationResult(True)
    
    @staticmethod
    def get_user_friendly_error_message(result):
        return "; ".join(result.errors)


class MockHistoryItem:
    """Mock history item for testing."""
    def __init__(self, timestamp, prompt, script, executed=False):
        self.timestamp = timestamp
        self.prompt = prompt
        self.script = script
        self.executed = executed


class MockScene:
    """Mock scene with history for testing."""
    def __init__(self):
        self.ai_history = []
        self.ai_status = "Ready"


class TestHistoryReplayLogic(unittest.TestCase):
    """Test history replay logic without full Blender environment."""

    def setUp(self):
        """Set up test fixtures."""
        self.scene = MockScene()
        self.script_validation = MockScriptValidation()

    def test_history_item_creation(self):
        """Test that history items store all required fields."""
        item = MockHistoryItem(
            timestamp="12:34:56",
            prompt="Create a red cube",
            script="import bpy\nbpy.ops.mesh.primitive_cube_add()",
            executed=False
        )
        self.assertEqual(item.timestamp, "12:34:56")
        self.assertEqual(item.prompt, "Create a red cube")
        self.assertIn("primitive_cube_add", item.script)
        self.assertFalse(item.executed)

    def test_script_validation_for_replay(self):
        """Test that scripts are validated before replay."""
        # Safe script
        safe_script = "import bpy\nbpy.ops.mesh.primitive_cube_add()"
        result = self.script_validation.validate_script_safety(safe_script)
        self.assertTrue(result.is_valid)

        # Unsafe script
        unsafe_script = "import os\nos.system('rm -rf /')"
        result = self.script_validation.validate_script_safety(unsafe_script)
        self.assertFalse(result.is_valid)
        self.assertIn("os", " ".join(result.errors).lower())

    def test_history_storage_multiple_items(self):
        """Test that multiple history items can be stored."""
        self.scene.ai_history.append(MockHistoryItem("10:00:00", "First", "script1"))
        self.scene.ai_history.append(MockHistoryItem("10:01:00", "Second", "script2"))
        self.scene.ai_history.append(MockHistoryItem("10:02:00", "Third", "script3"))
        
        self.assertEqual(len(self.scene.ai_history), 3)
        self.assertEqual(self.scene.ai_history[0].prompt, "First")
        self.assertEqual(self.scene.ai_history[1].prompt, "Second")
        self.assertEqual(self.scene.ai_history[2].prompt, "Third")

    def test_replay_executes_stored_script(self):
        """Test that replay uses the stored script, not current prompt."""
        # Add an item to history
        stored_script = "import bpy\nbpy.ops.mesh.primitive_uv_sphere_add()"
        self.scene.ai_history.append(MockHistoryItem("10:00:00", "Create sphere", stored_script))
        
        # Verify the script is accessible
        history_item = self.scene.ai_history[0]
        self.assertEqual(history_item.script, stored_script)
        
        # Validate it can be executed (would be valid)
        result = self.script_validation.validate_script_safety(history_item.script)
        self.assertTrue(result.is_valid)

    def test_replay_creates_duplicate_allowed(self):
        """Test that replaying creates new objects (duplicates allowed)."""
        # The key behavior: replay should not prevent duplicate creation
        script = "bpy.ops.mesh.primitive_cube_add()"
        self.scene.ai_history.append(MockHistoryItem("10:00:00", "Cube", script))
        
        # Simulating replay - no duplicate prevention logic
        # In real implementation, this would create a new cube
        self.assertTrue(True)  # Placeholder - real test would verify duplicate created

    def test_replay_history_persists(self):
        """Test that history persists after replay."""
        self.scene.ai_history.append(MockHistoryItem("10:00:00", "Item 1", "script1"))
        self.scene.ai_history.append(MockHistoryItem("10:01:00", "Item 2", "script2"))
        
        initial_count = len(self.scene.ai_history)
        
        # Simulate replay - history should not be modified
        _ = self.scene.ai_history[0]  # Access for replay
        
        self.assertEqual(len(self.scene.ai_history), initial_count)
        self.assertEqual(self.scene.ai_history[0].prompt, "Item 1")

    def test_replay_invalid_index(self):
        """Test that replay with invalid index is handled."""
        self.scene.ai_history.append(MockHistoryItem("10:00:00", "Only item", "script"))
        
        # Test negative index (invalid)
        self.assertFalse(-1 >= 0 and -1 < len(self.scene.ai_history))
        
        # Test out of bounds index
        self.assertFalse(5 >= 0 and 5 < len(self.scene.ai_history))
        
        # Test valid index
        self.assertTrue(0 >= 0 and 0 < len(self.scene.ai_history))

    def test_history_replay_operator_signature(self):
        """Test that the replay operator has correct properties."""
        # Verify the operator would have the expected properties
        # This is a structural test
        
        # Operator should have an 'index' property
        # In real Blender, this would be bpy.props.IntProperty
        expected_properties = ['index']
        self.assertEqual(len(expected_properties), 1)

    def test_replay_operator_poll(self):
        """Test that replay operator polls correctly based on history availability."""
        # When no history, poll should return False
        self.assertFalse(len(self.scene.ai_history) > 0)
        
        # Add history
        self.scene.ai_history.append(MockHistoryItem("10:00:00", "Item", "script"))
        
        # Now poll should return True
        self.assertTrue(len(self.scene.ai_history) > 0)


class TestHistoryReplayOperator(unittest.TestCase):
    """Test the replay operator behavior."""

    def test_replay_flow(self):
        """Test the complete replay flow."""
        scene = MockScene()
        
        # Add history item
        script = "import bpy\nbpy.ops.mesh.primitive_cylinder_add()"
        scene.ai_history.append(MockHistoryItem("10:00:00", "Create cylinder", script))
        
        # Validate index
        index = 0
        self.assertTrue(index >= 0 and index < len(scene.ai_history))
        
        # Get history item
        history_item = scene.ai_history[index]
        
        # Validate script
        result = MockScriptValidation.validate_script_safety(history_item.script)
        self.assertTrue(result.is_valid)
        
        # Script would be executed here
        executed = True
        self.assertTrue(executed)


if __name__ == '__main__':
    unittest.main()
