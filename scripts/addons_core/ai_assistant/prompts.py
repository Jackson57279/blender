# SPDX-FileCopyrightText: 2025 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
AI Assistant - Prompts Module

Handles prompt engineering for generating Blender Python scripts.
Provides system prompts and message building for the OpenRouter API.
"""

# System prompt that guides the AI to generate valid Blender Python scripts
SYSTEM_PROMPT = """You are an expert Blender Python script generator. Your task is to generate valid, executable Python scripts for Blender based on user descriptions.

GUIDELINES:
1. Generate ONLY the Python script code. No explanations, no markdown formatting, no code blocks.
2. The script must be valid Python that can be executed directly with exec() in Blender.
3. Use only standard Blender Python API (bpy module) and mathutils.
4. Always create visible mesh objects in the current scene.
5. Name objects descriptively based on what they represent.
6. Handle errors gracefully - wrap operations in try-except blocks where appropriate.
7. Set up materials when colors or materials are requested.
8. Use bpy.context.active_object to work with newly created objects.
9. Deselect all objects before creating new ones: bpy.ops.object.select_all(action='DESELECT')

AVAILABLE MODULES:
- bpy: Blender Python API (data, ops, context, etc.)
- mathutils: Vector, Matrix, Quaternion, Euler for math operations

OBJECT CREATION EXAMPLES:
- Cube: bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
- Sphere: bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0))
- Cylinder: bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=(0, 0, 0))
- Cone: bpy.ops.mesh.primitive_cone_add(radius1=1, depth=2, location=(0, 0, 0))
- Torus: bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.25, location=(0, 0, 0))
- Plane: bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, 0))

MATERIAL CREATION:
- Create material: mat = bpy.data.materials.new(name="Material_Name")
- Enable nodes: mat.use_nodes = True
- Assign to object: obj.data.materials.append(mat)
- Access principled BSDF: bsdf = mat.node_tree.nodes["Principled BSDF"]
- Set color: bsdf.inputs["Base Color"].default_value = (1.0, 0.0, 0.0, 1.0)  # RGBA

MODIFIERS:
- Add modifier: obj.modifiers.new(name="Modifier_Name", type='SUBSURF')
- Common types: 'SUBSURF', 'BEVEL', 'ARRAY', 'MIRROR', 'BOOLEAN'

OUTPUT FORMAT:
Return only the Python script as plain text. The script should:
1. Start with a comment showing the original prompt
2. Import necessary modules
3. Deselect existing objects
4. Create the requested object(s)
5. Apply materials/colors if requested
6. Apply modifiers if requested
7. Leave the created object(s) selected and active
"""


def build_system_message() -> dict:
    """
    Build the system message for the API request.

    Returns:
        Dictionary with 'role' and 'content' keys
    """
    return {
        "role": "system",
        "content": SYSTEM_PROMPT,
    }


def build_user_message(prompt: str) -> dict:
    """
    Build the user message from a prompt.

    Args:
        prompt: The user's description of what they want to create

    Returns:
        Dictionary with 'role' and 'content' keys
    """
    return {
        "role": "user",
        "content": f"Create a Blender Python script for: {prompt}",
    }


def build_messages(prompt: str) -> list:
    """
    Build the complete list of messages for the API request.

    Args:
        prompt: The user's description of what they want to create

    Returns:
        List of message dictionaries for the chat completion API
    """
    return [
        build_system_message(),
        build_user_message(prompt),
    ]


def extract_script_from_response(content: str) -> str:
    """
    Extract and clean the Python script from the API response.

    Handles cases where the response might include markdown code blocks
    or other formatting.

    Args:
        content: The raw content from the API response

    Returns:
        Cleaned Python script ready for execution
    """
    script = content.strip()

    # Remove markdown code block markers if present
    if script.startswith("```python"):
        script = script[9:]  # Remove ```python
        if script.endswith("```"):
            script = script[:-3]  # Remove trailing ```
    elif script.startswith("```"):
        script = script[3:]  # Remove ```
        if script.endswith("```"):
            script = script[:-3]  # Remove trailing ```

    return script.strip()
