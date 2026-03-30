# SPDX-FileCopyrightText: 2025 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
Tests for the Prompts module.

These tests verify the prompt engineering functionality including:
- System prompt structure
- Prompt template selection
- User prompt wrapping
- Generation type detection
- Message building
- Script extraction and validation
- Example scripts availability
"""

import sys
import unittest

# Add parent directory to path
sys.path.insert(0, '/home/dih/blender/scripts/addons_core/ai_assistant')

import prompts
from prompts import (
    SYSTEM_PROMPT,
    PROMPT_TEMPLATES,
    GENERATION_TYPE_KEYWORDS,
    build_system_message,
    build_user_message,
    build_messages,
    detect_generation_type,
    get_prompt_template,
    wrap_user_prompt,
    extract_script_from_response,
    validate_script_format,
    get_example_script,
    get_all_example_names,
)


class TestSystemPrompt(unittest.TestCase):
    """Test cases for the system prompt."""

    def test_system_prompt_exists(self):
        """Test that the system prompt is defined and non-empty."""
        self.assertIsNotNone(SYSTEM_PROMPT)
        self.assertGreater(len(SYSTEM_PROMPT), 1000)

    def test_system_prompt_contains_bpy_instructions(self):
        """Test that system prompt includes bpy API instructions."""
        self.assertIn("bpy", SYSTEM_PROMPT.lower())
        # Check for bpy module reference in the script structure
        self.assertIn("bpy", SYSTEM_PROMPT)

    def test_system_prompt_contains_material_instructions(self):
        """Test that system prompt includes material creation instructions."""
        self.assertIn("material", SYSTEM_PROMPT.lower())
        self.assertIn("Principled BSDF", SYSTEM_PROMPT)

    def test_system_prompt_contains_modifier_instructions(self):
        """Test that system prompt includes modifier instructions."""
        self.assertIn("modifier", SYSTEM_PROMPT.lower())
        self.assertIn("SUBSURF", SYSTEM_PROMPT)

    def test_system_prompt_enforces_no_markdown(self):
        """Test that system prompt instructs AI to avoid markdown."""
        self.assertIn("no markdown", SYSTEM_PROMPT.lower())
        self.assertIn("no code blocks", SYSTEM_PROMPT.lower())

    def test_system_prompt_includes_primitive_examples(self):
        """Test that system prompt includes primitive creation examples."""
        self.assertIn("primitive_cube_add", SYSTEM_PROMPT)
        self.assertIn("primitive_uv_sphere_add", SYSTEM_PROMPT)
        self.assertIn("primitive_cylinder_add", SYSTEM_PROMPT)


class TestPromptTemplates(unittest.TestCase):
    """Test cases for prompt templates."""

    def test_all_templates_exist(self):
        """Test that all generation type templates are defined."""
        expected_types = [
            "primitive", "material", "modifier", "complex",
            "multi_object", "animation", "lighting", "camera"
        ]
        for gen_type in expected_types:
            self.assertIn(gen_type, PROMPT_TEMPLATES)

    def test_templates_contain_description_placeholder(self):
        """Test that all templates contain the {description} placeholder."""
        for template in PROMPT_TEMPLATES.values():
            self.assertIn("{description}", template)

    def test_primitive_template_content(self):
        """Test primitive generation template content."""
        template = PROMPT_TEMPLATES["primitive"]
        self.assertIn("primitive", template.lower())
        self.assertIn("executable Python script", template)

    def test_material_template_content(self):
        """Test material generation template content."""
        template = PROMPT_TEMPLATES["material"]
        self.assertIn("material", template.lower())
        self.assertIn("RGB", template)
        self.assertIn("Principled BSDF", template)

    def test_modifier_template_content(self):
        """Test modifier generation template content."""
        template = PROMPT_TEMPLATES["modifier"]
        self.assertIn("modifier", template.lower())
        self.assertIn("SUBSURF", template)


class TestGenerationTypeDetection(unittest.TestCase):
    """Test cases for generation type detection."""

    def test_detect_primitive_type(self):
        """Test detection of primitive generation type."""
        self.assertEqual(detect_generation_type("Create a cube"), "primitive")
        self.assertEqual(detect_generation_type("Make a sphere"), "primitive")
        self.assertEqual(detect_generation_type("Add a cylinder"), "primitive")
        self.assertEqual(detect_generation_type("Generate a torus"), "primitive")

    def test_detect_material_type(self):
        """Test detection of material generation type."""
        # Pure color prompts should detect material type
        self.assertEqual(detect_generation_type("Make it red"), "material")
        self.assertEqual(detect_generation_type("Blue metallic object"), "material")
        self.assertEqual(detect_generation_type("Shiny object"), "material")
        self.assertEqual(detect_generation_type("Glowing green light"), "material")

    def test_detect_modifier_type(self):
        """Test detection of modifier generation type."""
        self.assertEqual(detect_generation_type("Subdivision surface"), "modifier")
        self.assertEqual(detect_generation_type("Add bevel modifier"), "modifier")
        self.assertEqual(detect_generation_type("Array of objects"), "modifier")

    def test_detect_complex_type(self):
        """Test detection of complex object type (default)."""
        self.assertEqual(detect_generation_type("Create a chair"), "complex")
        self.assertEqual(detect_generation_type("Build a house"), "complex")
        self.assertEqual(detect_generation_type("Make a car"), "complex")

    def test_detect_multi_object_type(self):
        """Test detection of multi-object generation type."""
        self.assertEqual(detect_generation_type("Create three objects"), "multi_object")
        self.assertEqual(detect_generation_type("A row of items"), "multi_object")

    def test_detect_animation_type(self):
        """Test detection of animation generation type."""
        self.assertEqual(detect_generation_type("Keyframe animation"), "animation")
        self.assertEqual(detect_generation_type("Orbit motion"), "animation")

    def test_detect_lighting_type(self):
        """Test detection of lighting generation type."""
        self.assertEqual(detect_generation_type("Add a point light"), "lighting")
        self.assertEqual(detect_generation_type("Create sun lighting"), "lighting")

    def test_detect_camera_type(self):
        """Test detection of camera generation type."""
        self.assertEqual(detect_generation_type("Set up a camera"), "camera")
        self.assertEqual(detect_generation_type("Create view from angle"), "camera")

    def test_type_keywords_mapping(self):
        """Test that keywords are mapped to correct types."""
        self.assertIn("cube", GENERATION_TYPE_KEYWORDS["primitive"])
        self.assertIn("red", GENERATION_TYPE_KEYWORDS["material"])
        self.assertIn("subdivision", GENERATION_TYPE_KEYWORDS["modifier"])
        self.assertIn("chair", GENERATION_TYPE_KEYWORDS["complex"])


class TestGetPromptTemplate(unittest.TestCase):
    """Test cases for getting prompt templates."""

    def test_get_existing_template(self):
        """Test getting an existing template."""
        template = get_prompt_template("material")
        self.assertIsNotNone(template)
        self.assertIn("material", template.lower())

    def test_get_default_for_unknown_type(self):
        """Test that unknown types return complex template."""
        template = get_prompt_template("unknown_type")
        self.assertEqual(template, PROMPT_TEMPLATES["complex"])


class TestWrapUserPrompt(unittest.TestCase):
    """Test cases for wrapping user prompts."""

    def test_wrap_with_auto_detection(self):
        """Test wrapping with automatic generation type detection."""
        wrapped = wrap_user_prompt("Create a shiny metallic cube")
        self.assertIn("Create a shiny metallic cube", wrapped)
        # "shiny" and "metallic" should trigger material template
        self.assertIn("material", wrapped.lower())

    def test_wrap_with_explicit_type(self):
        """Test wrapping with explicit generation type."""
        wrapped = wrap_user_prompt("Create a cube", gen_type="primitive")
        self.assertIn("Create a cube", wrapped)
        self.assertIn("primitive", wrapped.lower())

    def test_wrap_includes_instructions(self):
        """Test that wrapped prompt includes generation-specific instructions."""
        wrapped = wrap_user_prompt("Make something", gen_type="modifier")
        self.assertIn("modifier", wrapped.lower())
        self.assertIn("Generate only", wrapped)


class TestBuildSystemMessage(unittest.TestCase):
    """Test cases for building system messages."""

    def test_build_system_message_structure(self):
        """Test that system message has correct structure."""
        message = build_system_message()
        self.assertIn("role", message)
        self.assertIn("content", message)
        self.assertEqual(message["role"], "system")
        self.assertGreater(len(message["content"]), 1000)

    def test_system_message_content(self):
        """Test that system message contains necessary instructions."""
        message = build_system_message()
        content = message["content"]
        self.assertIn("bpy", content)
        self.assertIn("ONLY", content)


class TestBuildUserMessage(unittest.TestCase):
    """Test cases for building user messages."""

    def test_build_user_message_structure(self):
        """Test that user message has correct structure."""
        message = build_user_message("Create a red cube")
        self.assertIn("role", message)
        self.assertIn("content", message)
        self.assertEqual(message["role"], "user")

    def test_user_message_includes_prompt(self):
        """Test that user message includes the original prompt."""
        prompt = "Create a shiny blue sphere"
        message = build_user_message(prompt)
        self.assertIn("Create a shiny blue sphere", message["content"])

    def test_user_message_with_auto_detection(self):
        """Test that user message auto-detects generation type."""
        message = build_user_message("Create a metallic object")
        content = message["content"]
        # "metallic" should trigger material detection
        self.assertIn("material", content.lower())


class TestBuildMessages(unittest.TestCase):
    """Test cases for building complete message lists."""

    def test_build_messages_returns_list(self):
        """Test that build_messages returns a list."""
        messages = build_messages("Create a cube")
        self.assertIsInstance(messages, list)
        self.assertEqual(len(messages), 2)

    def test_build_messages_has_system_and_user(self):
        """Test that messages include system and user messages."""
        messages = build_messages("Create a cube")
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[1]["role"], "user")

    def test_build_messages_with_explicit_type(self):
        """Test building messages with explicit generation type."""
        messages = build_messages("Create a cube", gen_type="primitive")
        self.assertEqual(len(messages), 2)
        self.assertIn("primitive", messages[1]["content"].lower())


class TestExtractScriptFromResponse(unittest.TestCase):
    """Test cases for extracting scripts from API responses."""

    def test_extract_plain_script(self):
        """Test extracting script without markdown."""
        content = "import bpy\nbpy.ops.mesh.primitive_cube_add()"
        result = extract_script_from_response(content)
        self.assertEqual(result, content)

    def test_extract_python_code_block(self):
        """Test extracting script from python markdown block."""
        content = "```python\nimport bpy\nbpy.ops.mesh.primitive_cube_add()\n```"
        result = extract_script_from_response(content)
        self.assertEqual(result, "import bpy\nbpy.ops.mesh.primitive_cube_add()")

    def test_extract_generic_code_block(self):
        """Test extracting script from generic markdown block."""
        content = "```\nimport bpy\nbpy.ops.mesh.primitive_cube_add()\n```"
        result = extract_script_from_response(content)
        self.assertEqual(result, "import bpy\nbpy.ops.mesh.primitive_cube_add()")

    def test_extract_removes_explanatory_text(self):
        """Test that explanatory text is removed from script."""
        content = "import bpy\n# code\n\nThis is an explanation"
        result = extract_script_from_response(content)
        self.assertNotIn("This is an explanation", result)

    def test_extract_handles_empty_response(self):
        """Test handling of empty response."""
        result = extract_script_from_response("")
        self.assertEqual(result, "")


class TestValidateScriptFormat(unittest.TestCase):
    """Test cases for script format validation."""

    def test_validate_valid_script(self):
        """Test validating a valid Python script."""
        script = "import bpy\nbpy.ops.mesh.primitive_cube_add()"
        is_valid, error = validate_script_format(script)
        self.assertTrue(is_valid)
        self.assertEqual(error, "")

    def test_validate_empty_script(self):
        """Test validating empty script."""
        is_valid, error = validate_script_format("")
        self.assertFalse(is_valid)
        self.assertEqual(error, "Empty script received")

    def test_validate_no_bpy_script(self):
        """Test validating script without bpy usage."""
        script = "print('hello')"
        is_valid, error = validate_script_format(script)
        self.assertFalse(is_valid)
        self.assertIn("Blender API", error)

    def test_validate_syntax_error(self):
        """Test validating script with syntax error."""
        script = "import bpy\nif True"  # Incomplete if statement
        is_valid, error = validate_script_format(script)
        self.assertFalse(is_valid)
        self.assertIn("Syntax error", error)


class TestExampleScripts(unittest.TestCase):
    """Test cases for example scripts."""

    def test_get_example_names(self):
        """Test getting list of example script names."""
        names = get_all_example_names()
        self.assertIsInstance(names, list)
        self.assertGreater(len(names), 0)

    def test_get_existing_example(self):
        """Test retrieving an existing example script."""
        script = get_example_script("red_cube")
        self.assertIsNotNone(script)
        self.assertIn("import bpy", script)
        self.assertIn("RedCube", script)

    def test_get_nonexistent_example(self):
        """Test retrieving a non-existent example script."""
        script = get_example_script("nonexistent")
        self.assertIsNone(script)

    def test_example_scripts_are_valid_python(self):
        """Test that all example scripts are valid Python."""
        for name in get_all_example_names():
            script = get_example_script(name)
            self.assertIsNotNone(script)
            try:
                compile(script, '<string>', 'exec')
            except SyntaxError as e:
                self.fail(f"Example script '{name}' has syntax error: {e}")

    def test_example_scripts_use_bpy(self):
        """Test that all example scripts use bpy."""
        for name in get_all_example_names():
            script = get_example_script(name)
            self.assertIsNotNone(script)
            self.assertIn("bpy", script)


class TestIntegration(unittest.TestCase):
    """Integration tests for the prompts module."""

    def test_full_prompt_pipeline(self):
        """Test the full prompt building and extraction pipeline."""
        # Simulate a user request
        user_prompt = "Create a red cube with beveled edges"

        # Build messages for API
        messages = build_messages(user_prompt)

        # Verify structure
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[1]["role"], "user")

        # The user message should contain material and modifier hints
        user_content = messages[1]["content"]
        self.assertIn("red", user_content.lower())

    def test_generation_type_consistency(self):
        """Test that generation type detection is consistent with keywords."""
        for gen_type, keywords in GENERATION_TYPE_KEYWORDS.items():
            for keyword in keywords[:2]:  # Test first 2 keywords of each type
                detected = detect_generation_type(f"Create {keyword} object")
                # The detected type should match or be related to the keyword's type
                self.assertEqual(detected, gen_type)


if __name__ == '__main__':
    unittest.main(verbosity=2)
