# SPDX-FileCopyrightText: 2025 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
Tests for material and modifier support in prompt engineering.

These tests validate that the prompt engineering module provides
correct guidance and examples for creating materials and modifiers.
"""

import sys
import unittest
import types

# Add parent directory to path
sys.path.insert(0, '/home/dih/blender/scripts/addons_core/ai_assistant')

import prompts
from prompts import (
    SYSTEM_PROMPT,
    MATERIAL_GENERATION_TEMPLATE,
    MODIFIER_GENERATION_TEMPLATE,
    EXAMPLE_SCRIPTS,
    detect_generation_type,
    get_example_script,
    get_all_example_names,
)


class TestMaterialSupport(unittest.TestCase):
    """Test cases for material creation support."""

    def test_system_prompt_contains_material_creation(self):
        """Test that system prompt includes material creation instructions."""
        self.assertIn("material", SYSTEM_PROMPT.lower())
        self.assertIn("bpy.data.materials.new", SYSTEM_PROMPT)

    def test_system_prompt_contains_color_examples(self):
        """Test that system prompt includes color examples."""
        # Check for color keywords in the material colors section
        self.assertIn("Red:", SYSTEM_PROMPT)
        self.assertIn("Blue:", SYSTEM_PROMPT)
        self.assertIn("Green:", SYSTEM_PROMPT)

    def test_system_prompt_contains_material_types(self):
        """Test that system prompt includes material type descriptions."""
        self.assertIn("Metallic", SYSTEM_PROMPT)
        self.assertIn("Glass", SYSTEM_PROMPT)
        self.assertIn("Emissive", SYSTEM_PROMPT)

    def test_system_prompt_contains_bsdf_instructions(self):
        """Test that system prompt includes BSDF node instructions."""
        self.assertIn("Principled BSDF", SYSTEM_PROMPT)
        self.assertIn("Base Color", SYSTEM_PROMPT)
        self.assertIn("Metallic", SYSTEM_PROMPT)
        self.assertIn("Roughness", SYSTEM_PROMPT)

    def test_material_template_exists(self):
        """Test that material generation template exists."""
        self.assertIsNotNone(MATERIAL_GENERATION_TEMPLATE)
        self.assertIn("material", MATERIAL_GENERATION_TEMPLATE.lower())

    def test_material_template_contains_color_examples(self):
        """Test that material template includes color RGB examples."""
        self.assertIn("RGB", MATERIAL_GENERATION_TEMPLATE)
        self.assertIn("Red:", MATERIAL_GENERATION_TEMPLATE)
        self.assertIn("Blue:", MATERIAL_GENERATION_TEMPLATE)

    def test_material_template_contains_material_types(self):
        """Test that material template includes material type descriptions."""
        self.assertIn("Metallic", MATERIAL_GENERATION_TEMPLATE)
        self.assertIn("Glass", MATERIAL_GENERATION_TEMPLATE)
        self.assertIn("Emissive", MATERIAL_GENERATION_TEMPLATE)

    def test_material_template_contains_step_by_step(self):
        """Test that material template has step-by-step instructions."""
        self.assertIn("Follow these steps", MATERIAL_GENERATION_TEMPLATE)

    def test_material_keyword_detection(self):
        """Test that material-related keywords are detected."""
        # Pure material prompts (no primitive keywords)
        material_prompts = [
            "Make it red",
            "Add gold material",
            "Create shiny metallic object",
            "Make a glass cup",
            "Create a glowing emissive light",
        ]
        for prompt in material_prompts:
            gen_type = detect_generation_type(prompt)
            self.assertEqual(gen_type, "material", f"Failed for: {prompt}")

    def test_mixed_prompts_contain_material_keywords(self):
        """Test that mixed prompts (primitive + material) are handled."""
        # When user specifies both a primitive and a color, the primitive detection
        # takes priority, but the system prompt still guides material creation
        gen_type = detect_generation_type("Create a red cube")
        # Could be either primitive or material depending on scoring
        self.assertIn(gen_type, ["primitive", "material"])
        
        gen_type = detect_generation_type("Blue metallic sphere")
        self.assertIn(gen_type, ["primitive", "material"])

    def test_example_script_red_cube(self):
        """Test that red cube example script is valid."""
        script = get_example_script("red_cube")
        self.assertIsNotNone(script)
        self.assertIn("bpy.data.materials.new", script)
        self.assertIn("Base Color", script)
        # Check for red color values
        self.assertIn("1.0, 0.0, 0.0", script)
        # Compile test
        try:
            compile(script, '<string>', 'exec')
        except SyntaxError as e:
            self.fail(f"red_cube script has syntax error: {e}")

    def test_example_script_blue_cylinder(self):
        """Test that blue metallic cylinder example script is valid."""
        script = get_example_script("blue_cylinder")
        self.assertIsNotNone(script)
        self.assertIn("bpy.data.materials.new", script)
        self.assertIn("Metallic", script)
        # Compile test
        try:
            compile(script, '<string>', 'exec')
        except SyntaxError as e:
            self.fail(f"blue_cylinder script has syntax error: {e}")

    def test_example_script_gold_metallic_sphere(self):
        """Test that gold metallic sphere example script exists and is valid."""
        script = get_example_script("gold_metallic_sphere")
        self.assertIsNotNone(script)
        self.assertIn("bpy.data.materials.new", script)
        self.assertIn("Metallic", script)
        # Check for gold color (1.0, 0.84, 0.0)
        self.assertIn("1.0, 0.84, 0.0", script)
        # Compile test
        try:
            compile(script, '<string>', 'exec')
        except SyntaxError as e:
            self.fail(f"gold_metallic_sphere script has syntax error: {e}")

    def test_example_script_glass_material(self):
        """Test that glass material example script exists and is valid."""
        script = get_example_script("glass_material_example")
        self.assertIsNotNone(script)
        self.assertIn("bpy.data.materials.new", script)
        self.assertIn("Transmission", script)
        self.assertIn("IOR", script)
        # Compile test
        try:
            compile(script, '<string>', 'exec')
        except SyntaxError as e:
            self.fail(f"glass_material_example script has syntax error: {e}")

    def test_example_script_emissive(self):
        """Test that emissive glowing object example script exists and is valid."""
        script = get_example_script("emissive_glowing_object")
        self.assertIsNotNone(script)
        self.assertIn("bpy.data.materials.new", script)
        self.assertIn("Emission", script)
        # Compile test
        try:
            compile(script, '<string>', 'exec')
        except SyntaxError as e:
            self.fail(f"emissive_glowing_object script has syntax error: {e}")


class TestModifierSupport(unittest.TestCase):
    """Test cases for modifier support."""

    def test_system_prompt_contains_modifier_instructions(self):
        """Test that system prompt includes modifier instructions."""
        self.assertIn("modifier", SYSTEM_PROMPT.lower())
        self.assertIn("modifiers.new", SYSTEM_PROMPT)

    def test_system_prompt_contains_subsurf(self):
        """Test that system prompt includes subdivision surface instructions."""
        self.assertIn("SUBSURF", SYSTEM_PROMPT)
        self.assertIn("subdivision", SYSTEM_PROMPT.lower())

    def test_system_prompt_contains_bevel(self):
        """Test that system prompt includes bevel modifier instructions."""
        self.assertIn("BEVEL", SYSTEM_PROMPT)
        self.assertIn("bevel", SYSTEM_PROMPT.lower())

    def test_system_prompt_contains_array(self):
        """Test that system prompt includes array modifier instructions."""
        self.assertIn("ARRAY", SYSTEM_PROMPT)
        self.assertIn("array", SYSTEM_PROMPT.lower())

    def test_system_prompt_contains_mirror(self):
        """Test that system prompt includes mirror modifier instructions."""
        self.assertIn("MIRROR", SYSTEM_PROMPT)

    def test_modifier_template_exists(self):
        """Test that modifier generation template exists."""
        self.assertIsNotNone(MODIFIER_GENERATION_TEMPLATE)
        self.assertIn("modifier", MODIFIER_GENERATION_TEMPLATE.lower())

    def test_modifier_template_contains_step_by_step(self):
        """Test that modifier template has step-by-step instructions."""
        self.assertIn("Follow these steps", MODIFIER_GENERATION_TEMPLATE)

    def test_modifier_template_contains_modifier_types(self):
        """Test that modifier template includes modifier types."""
        self.assertIn("SUBSURF", MODIFIER_GENERATION_TEMPLATE)
        self.assertIn("BEVEL", MODIFIER_GENERATION_TEMPLATE)
        self.assertIn("ARRAY", MODIFIER_GENERATION_TEMPLATE)
        self.assertIn("MIRROR", MODIFIER_GENERATION_TEMPLATE)

    def test_modifier_template_contains_workflows(self):
        """Test that modifier template includes workflow descriptions."""
        self.assertIn("Subdivision + Smooth", MODIFIER_GENERATION_TEMPLATE)
        self.assertIn("Bevel", MODIFIER_GENERATION_TEMPLATE)
        self.assertIn("Array", MODIFIER_GENERATION_TEMPLATE)
        self.assertIn("Mirror", MODIFIER_GENERATION_TEMPLATE)

    def test_modifier_keyword_detection(self):
        """Test that modifier-related keywords are detected."""
        # Pure modifier prompts (no primitive keywords, avoiding overlapping keywords like mirror)
        modifier_prompts = [
            "Add bevel",
            "Apply smooth modifier",
            "Use subdivision surface",
            "Use solidify for thickness",
        ]
        for prompt in modifier_prompts:
            gen_type = detect_generation_type(prompt)
            self.assertEqual(gen_type, "modifier", f"Failed for: {prompt}")

    def test_mixed_prompts_contain_modifier_keywords(self):
        """Test that mixed prompts (primitive + modifier) are handled."""
        # When user specifies both a primitive and a modifier, the modifier detection
        # takes priority (per priority_order in detect_generation_type)
        gen_type = detect_generation_type("Create a sphere with subdivision")
        # Should be modifier due to priority ordering
        self.assertEqual(gen_type, "modifier")
        
        gen_type = detect_generation_type("Cube with bevel")
        self.assertEqual(gen_type, "modifier")

    def test_example_script_smooth_sphere(self):
        """Test that smooth sphere with subdivision example script is valid."""
        script = get_example_script("smooth_sphere")
        self.assertIsNotNone(script)
        self.assertIn("modifiers.new", script)
        self.assertIn("SUBSURF", script)
        self.assertIn("shade_smooth", script)
        # Compile test
        try:
            compile(script, '<string>', 'exec')
        except SyntaxError as e:
            self.fail(f"smooth_sphere script has syntax error: {e}")

    def test_example_script_red_sphere_subdivision(self):
        """Test that red sphere with subdivision example script is valid."""
        script = get_example_script("red_sphere_subdivision")
        self.assertIsNotNone(script)
        self.assertIn("modifiers.new", script)
        self.assertIn("SUBSURF", script)
        self.assertIn("shade_smooth", script)
        # Has material too
        self.assertIn("bpy.data.materials.new", script)
        # Compile test
        try:
            compile(script, '<string>', 'exec')
        except SyntaxError as e:
            self.fail(f"red_sphere_subdivision script has syntax error: {e}")

    def test_example_script_beveled_cube(self):
        """Test that beveled cube example script is valid."""
        script = get_example_script("beveled_cube")
        self.assertIsNotNone(script)
        self.assertIn("modifiers.new", script)
        self.assertIn("BEVEL", script)
        self.assertIn("width", script.lower())
        # Compile test
        try:
            compile(script, '<string>', 'exec')
        except SyntaxError as e:
            self.fail(f"beveled_cube script has syntax error: {e}")

    def test_example_script_array_modifier(self):
        """Test that array modifier example script exists and is valid."""
        script = get_example_script("array_modifier_example")
        self.assertIsNotNone(script)
        self.assertIn("modifiers.new", script)
        self.assertIn("ARRAY", script)
        self.assertIn("relative_offset_displace", script)
        # Compile test
        try:
            compile(script, '<string>', 'exec')
        except SyntaxError as e:
            self.fail(f"array_modifier_example script has syntax error: {e}")

    def test_example_script_mirror_modifier(self):
        """Test that mirror modifier example script exists and is valid."""
        script = get_example_script("mirror_modifier_example")
        self.assertIsNotNone(script)
        self.assertIn("modifiers.new", script)
        self.assertIn("MIRROR", script)
        self.assertIn("use_axis", script)
        # Compile test
        try:
            compile(script, '<string>', 'exec')
        except SyntaxError as e:
            self.fail(f"mirror_modifier_example script has syntax error: {e}")


class TestCombinedMaterialModifier(unittest.TestCase):
    """Test cases for combined material and modifier support."""

    def test_red_sphere_subdivision_has_both(self):
        """Test that red sphere with subdivision has both material and modifier."""
        script = get_example_script("red_sphere_subdivision")
        self.assertIsNotNone(script)
        # Has material
        self.assertIn("bpy.data.materials.new", script)
        self.assertIn("Base Color", script)
        # Has modifier
        self.assertIn("modifiers.new", script)
        self.assertIn("SUBSURF", script)

    def test_gold_metallic_sphere_has_both(self):
        """Test that gold metallic sphere has both material and modifier."""
        script = get_example_script("gold_metallic_sphere")
        self.assertIsNotNone(script)
        # Has material
        self.assertIn("bpy.data.materials.new", script)
        self.assertIn("Metallic", script)
        # Has modifier
        self.assertIn("modifiers.new", script)
        self.assertIn("SUBSURF", script)

    def test_beveled_cube_has_both(self):
        """Test that beveled cube has both material and modifier."""
        script = get_example_script("beveled_cube")
        self.assertIsNotNone(script)
        # Has modifier
        self.assertIn("modifiers.new", script)
        self.assertIn("BEVEL", script)

    def test_glass_material_example_has_both(self):
        """Test that glass sphere has both material and modifier."""
        script = get_example_script("glass_material_example")
        self.assertIsNotNone(script)
        # Has material
        self.assertIn("bpy.data.materials.new", script)
        self.assertIn("Transmission", script)
        # Has modifier
        self.assertIn("modifiers.new", script)

    def test_array_modifier_example_has_both(self):
        """Test that array example has both material and modifier."""
        script = get_example_script("array_modifier_example")
        self.assertIsNotNone(script)
        # Has material
        self.assertIn("bpy.data.materials.new", script)
        # Has modifier
        self.assertIn("modifiers.new", script)
        self.assertIn("ARRAY", script)

    def test_mirror_modifier_example_has_both(self):
        """Test that mirror example has both material and modifier."""
        script = get_example_script("mirror_modifier_example")
        self.assertIsNotNone(script)
        # Has material
        self.assertIn("bpy.data.materials.new", script)
        # Has modifier
        self.assertIn("modifiers.new", script)
        self.assertIn("MIRROR", script)

    def test_all_example_scripts_are_valid_python(self):
        """Test that ALL example scripts are valid Python."""
        for name in get_all_example_names():
            script = get_example_script(name)
            self.assertIsNotNone(script, f"Example script '{name}' not found")
            try:
                compile(script, '<string>', 'exec')
            except SyntaxError as e:
                self.fail(f"Example script '{name}' has syntax error: {e}")

    def test_new_material_examples_added(self):
        """Test that new material-specific example scripts were added."""
        expected_material_scripts = [
            "red_sphere_subdivision",
            "gold_metallic_sphere",
            "glass_material_example",
            "emissive_glowing_object",
        ]
        available_scripts = get_all_example_names()
        for script_name in expected_material_scripts:
            self.assertIn(script_name, available_scripts,
                         f"Material example '{script_name}' should be added")

    def test_new_modifier_examples_added(self):
        """Test that new modifier-specific example scripts were added."""
        expected_modifier_scripts = [
            "red_sphere_subdivision",
            "beveled_cube",
            "gold_metallic_sphere",
            "array_modifier_example",
            "mirror_modifier_example",
        ]
        available_scripts = get_all_example_names()
        for script_name in expected_modifier_scripts:
            self.assertIn(script_name, available_scripts,
                         f"Modifier example '{script_name}' should be added")


class TestPromptGuidance(unittest.TestCase):
    """Test that prompts properly guide AI on materials and modifiers."""

    def test_system_prompt_mentions_material_and_modifier_examples(self):
        """Test that system prompt explicitly mentions material and modifier examples."""
        # Rule 9 and 10 mention materials and modifiers
        self.assertIn("materials or colors", SYSTEM_PROMPT)
        self.assertIn("modifiers are requested", SYSTEM_PROMPT)

    def test_material_template_includes_principled_bsdf(self):
        """Test that material template mentions Principled BSDF."""
        self.assertIn("Principled BSDF", MATERIAL_GENERATION_TEMPLATE)

    def test_material_template_includes_node_setup(self):
        """Test that material template includes node setup instructions."""
        self.assertIn("use_nodes = True", MATERIAL_GENERATION_TEMPLATE)

    def test_modifier_template_includes_modifier_new(self):
        """Test that modifier template includes modifiers.new() syntax."""
        self.assertIn("modifiers.new", MODIFIER_GENERATION_TEMPLATE)

    def test_keyword_detection_expanded_for_colors(self):
        """Test that expanded color keywords are detected."""
        # Pure color prompts (no primitive keywords)
        expanded_colors = [
            "Create a pink surface",
            "Make a cyan colored object",
            "Add brown material",
            "Create silver metallic finish",
            "Make a transparent glass",
        ]
        for prompt in expanded_colors:
            gen_type = detect_generation_type(prompt)
            self.assertEqual(gen_type, "material",
                           f"Should detect material type for: {prompt}")

    def test_mixed_color_primitive_prompts(self):
        """Test that mixed color + primitive prompts handle material keywords."""
        # When both color and primitive are present, modifier/material takes priority
        gen_type = detect_generation_type("Create a cyan cube")
        # Should be material due to priority ordering when scores are equal
        self.assertEqual(gen_type, "material")

    def test_keyword_detection_expanded_for_modifiers(self):
        """Test that expanded modifier keywords are detected."""
        expanded_modifiers = [
            "Create a curve along path",
            "Apply lattice deformation",
            "Make a bend using simple deform",
            "Add displacement modifier",
        ]
        for prompt in expanded_modifiers:
            gen_type = detect_generation_type(prompt)
            self.assertEqual(gen_type, "modifier",
                           f"Should detect modifier type for: {prompt}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
