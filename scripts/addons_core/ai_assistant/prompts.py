# SPDX-FileCopyrightText: 2025 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
AI Assistant - Prompt Engineering Module

Handles prompt engineering for generating Blender Python scripts.
Provides system prompts, prompt templates for different generation types,
and message building for the OpenRouter API.
"""

from typing import Dict, List, Optional

# =============================================================================
# SYSTEM PROMPT - Core instructions for AI script generation
# =============================================================================

SYSTEM_PROMPT = """You are an expert Blender Python API (bpy) specialist. Your sole purpose is to generate valid, executable Python scripts for Blender based on user descriptions.

CRITICAL RULES:
1. Generate ONLY the Python script code. No markdown, no explanations, no code blocks (```), no conversational text.
2. The script must be valid Python that can be executed directly with exec() in Blender's Python environment.
3. Use ONLY bpy and mathutils modules. No external libraries, no file I/O, no network calls.
4. Always create VISIBLE mesh objects in the current scene.
5. Objects must have DESCRIPTIVE names based on what they represent.
6. ALWAYS deselect all objects before creating new ones: bpy.ops.object.select_all(action='DESELECT')
7. ALWAYS select the newly created object(s) and make them active at the end.
8. Handle errors gracefully - use try-except only when necessary.
9. When materials or colors are requested, create and assign them properly.
10. When modifiers are requested, add them with sensible default settings.

AVAILABLE BLENDER API MODULES:
- bpy: Blender Python API
  - bpy.ops.mesh: Mesh primitives (cube_add, uv_sphere_add, cylinder_add, etc.)
  - bpy.ops.object: Object operations (select_all, delete, etc.)
  - bpy.data: Data access (meshes, objects, materials, collections)
  - bpy.context: Current context (scene, active_object, selected_objects)
- mathutils: Mathematical utilities
  - Vector: 3D vectors for locations, rotations
  - Matrix: Transformation matrices
  - Euler: Euler angle rotations
  - Quaternion: Quaternion rotations

PRIMITIVE OBJECT CREATION (bpy.ops.mesh):
- Cube: primitive_cube_add(size=2, location=(0, 0, 0))
- UV Sphere: primitive_uv_sphere_add(radius=1, location=(0, 0, 0), segments=32, ring_count=16)
- ICO Sphere: primitive_ico_sphere_add(radius=1, location=(0, 0, 0), subdivisions=2)
- Cylinder: primitive_cylinder_add(radius=1, depth=2, location=(0, 0, 0), vertices=32)
- Cone: primitive_cone_add(radius1=1, depth=2, location=(0, 0, 0), vertices=32)
- Torus: primitive_torus_add(major_radius=1, minor_radius=0.25, location=(0, 0, 0))
- Plane: primitive_plane_add(size=2, location=(0, 0, 0))
- Circle: primitive_circle_add(radius=1, location=(0, 0, 0), vertices=32)
- Grid: primitive_grid_add(x_subdivisions=10, y_subdivisions=10, size=2, location=(0, 0, 0))
- Monkey (Suzanne): primitive_monkey_add(size=2, location=(0, 0, 0))

OBJECT MANAGEMENT:
- Deselect all: bpy.ops.object.select_all(action='DESELECT')
- Select object: obj.select_set(True)
- Make active: bpy.context.view_layer.objects.active = obj
- Delete selected: bpy.ops.object.delete()
- Rename: obj.name = "NewName"
- Set location: obj.location = (x, y, z)
- Set rotation: obj.rotation_euler = (rx, ry, rz)  # in radians
- Set scale: obj.scale = (sx, sy, sz)

MATERIAL CREATION:
- Create material: mat = bpy.data.materials.new(name="MaterialName")
- Enable nodes: mat.use_nodes = True
- Assign to object: obj.data.materials.append(mat)
- Get BSDF node: bsdf = mat.node_tree.nodes["Principled BSDF"]
- Set base color: bsdf.inputs["Base Color"].default_value = (r, g, b, 1.0)  # RGB 0-1
- Set metallic: bsdf.inputs["Metallic"].default_value = 0.0-1.0
- Set roughness: bsdf.inputs["Roughness"].default_value = 0.0-1.0
- Set emission: bsdf.inputs["Emission"].default_value = (r, g, b, 1.0)

MODIFIER TYPES (obj.modifiers.new()):
- Subdivision Surface: type='SUBSURF', levels=2
- Bevel: type='BEVEL', width=0.02, segments=2
- Array: type='ARRAY', count=3, relative_offset_displace=(1, 0, 0)
- Mirror: type='MIRROR', use_axis=(True, False, False)
- Boolean: type='BOOLEAN', operation='DIFFERENCE'
- Solidify: type='SOLIDIFY', thickness=0.01
- Displace: type='DISPLACE'
- Smooth: type='SMOOTH'

SCRIPT STRUCTURE:
1. Import statement (only bpy and mathutils if needed)
2. Comment showing original user request
3. Deselect all existing objects
4. Create requested object(s)
5. Configure materials/colors if requested
6. Apply modifiers if requested
7. Select and activate the new object(s)
8. Update the view layer

OUTPUT FORMAT:
Return ONLY the Python script as plain text. No markdown, no explanation, no code fences. Just the executable Python code."""

# =============================================================================
# PROMPT TEMPLATES - Specialized prompts for different generation types
# =============================================================================

PRIMITIVE_GENERATION_TEMPLATE = """Create a Blender Python script that generates: {description}

This is for creating basic geometric primitives. Ensure:
1. Use the appropriate bpy.ops.mesh.primitive_*_add() operator
2. Set sensible default dimensions
3. Position at origin (0, 0, 0) unless specified otherwise
4. Give the object a descriptive name

Generate only the executable Python script."""

MATERIAL_GENERATION_TEMPLATE = """Create a Blender Python script that generates: {description}

This involves creating materials. Ensure:
1. Create a new material with a descriptive name
2. Enable nodes: mat.use_nodes = True
3. Access the Principled BSDF node
4. Set appropriate color values (RGB 0.0-1.0)
5. Set metallic and roughness properties as appropriate
6. Assign the material to the object

For common colors:
- Red: (1.0, 0.0, 0.0, 1.0)
- Green: (0.0, 1.0, 0.0, 1.0)
- Blue: (0.0, 0.0, 1.0, 1.0)
- Yellow: (1.0, 1.0, 0.0, 1.0)
- White: (1.0, 1.0, 1.0, 1.0)
- Black: (0.0, 0.0, 0.0, 1.0)
- Orange: (1.0, 0.5, 0.0, 1.0)
- Purple: (0.5, 0.0, 1.0, 1.0)

Generate only the executable Python script."""

MODIFIER_GENERATION_TEMPLATE = """Create a Blender Python script that generates: {description}

This involves using modifiers. Ensure:
1. Create the base mesh object first
2. Use obj.modifiers.new(name="ModifierName", type='MODTYPE')
3. Configure modifier properties appropriately
4. Common modifier types: SUBSURF (subdivision), BEVEL, ARRAY, MIRROR

For subdivision surface:
- Start with a cube or sphere with enough geometry
- Set levels=2 or 3 for smooth results

For bevel:
- Set width appropriate to object size
- Use segments=2 or more for rounded edges

Generate only the executable Python script."""

COMPLEX_OBJECT_TEMPLATE = """Create a Blender Python script that generates: {description}

This is a complex object request. Ensure:
1. Build the object from appropriate primitives or create mesh data programmatically
2. For multi-part objects, create each part with descriptive names
3. Use collections or parenting if logical grouping is needed
4. Apply appropriate materials to each part
5. Position parts correctly relative to each other

If creating detailed geometry:
- Use bpy.data.meshes.new() and bpy.data.objects.new() for manual mesh construction
- Define vertices, edges, faces for custom shapes
- Or combine primitives using boolean operations if appropriate

Generate only the executable Python script."""

MULTI_OBJECT_TEMPLATE = """Create a Blender Python script that generates: {description}

This request involves multiple objects. Ensure:
1. Create each object with a unique, descriptive name
2. Position objects relative to each other appropriately
3. If the objects form a logical group, organize them appropriately
4. Each object should be selectable and manipulable independently
5. Leave all created objects selected at the end

For arrays or patterns:
- Use the Array modifier for repeated geometry, OR
- Create multiple objects in a loop with calculated positions

Generate only the executable Python script."""

ANIMATION_TEMPLATE = """Create a Blender Python script that generates: {description}

This involves animation. Ensure:
1. Create the base object(s) first
2. Set initial keyframes using obj.keyframe_insert()
3. Change frame with bpy.context.scene.frame_set(frame_number)
4. Modify object properties (location, rotation, scale)
5. Insert additional keyframes

Common keyframe data paths:
- "location" for position
- "rotation_euler" for rotation
- "scale" for scaling

Generate only the executable Python script."""

LIGHTING_TEMPLATE = """Create a Blender Python script that generates: {description}

This involves lighting. Ensure:
1. Create appropriate light types (POINT, SUN, SPOT, AREA)
2. Position lights effectively for the scene
3. Set light energy/power appropriately
4. Configure light color if specified

Light types (bpy.ops.object.light_add):
- Point: type='POINT', suitable for local illumination
- Sun: type='SUN', for directional daylight
- Spot: type='SPOT', for focused lighting
- Area: type='AREA', for soft, diffused lighting

Generate only the executable Python script."""

CAMERA_TEMPLATE = """Create a Blender Python script that generates: {description}

This involves camera setup. Ensure:
1. Create camera with bpy.ops.object.camera_add()
2. Position camera to view the subject effectively
3. Point camera at the object or scene center
4. Make it the active camera if appropriate: bpy.context.scene.camera = cam

Camera considerations:
- Typical focal length: 50mm (use lens property)
- Position: use location and rotation, or look_at approach
- For turntable views: position camera at radius around center

Generate only the executable Python script."""

# Mapping of generation types to templates
PROMPT_TEMPLATES = {
    "primitive": PRIMITIVE_GENERATION_TEMPLATE,
    "material": MATERIAL_GENERATION_TEMPLATE,
    "modifier": MODIFIER_GENERATION_TEMPLATE,
    "complex": COMPLEX_OBJECT_TEMPLATE,
    "multi_object": MULTI_OBJECT_TEMPLATE,
    "animation": ANIMATION_TEMPLATE,
    "lighting": LIGHTING_TEMPLATE,
    "camera": CAMERA_TEMPLATE,
}

# Keywords that hint at generation type
GENERATION_TYPE_KEYWORDS = {
    "primitive": ["cube", "sphere", "cylinder", "cone", "torus", "plane", "circle", "grid", "monkey", "suzanne"],
    "material": ["red", "blue", "green", "color", "material", "texture", "shiny", "metallic", "matte", "rough", "emissive", "glowing"],
    "modifier": ["smooth", "subdivision", "subsurf", "bevel", "rounded", "array", "mirror", "duplicate", "solid", "thickness"],
    "complex": ["chair", "table", "car", "house", "building", "furniture", "detailed", "complex", "detailed"],
    "multi_object": ["three", "five", "ten", "multiple", "several", "row", "grid", "pattern", "array", "many", "few"],
    "animation": ["animate", "rotate", "spin", "move", "bounce", "swing", "orbit", "keyframe", "motion"],
    "lighting": ["light", "lamp", "illuminate", "bright", "shadow", "sun", "point light", "spotlight"],
    "camera": ["camera", "view", "angle", "shot", "perspective", "look at"],
}


def detect_generation_type(prompt: str) -> str:
    """
    Analyze the user prompt to determine the best generation type.

    Args:
        prompt: The user's description of what they want to create

    Returns:
        The detected generation type key (defaults to "complex")
    """
    prompt_lower = prompt.lower()

    # Count keyword matches for each type
    type_scores = {}
    for gen_type, keywords in GENERATION_TYPE_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in prompt_lower)
        if score > 0:
            type_scores[gen_type] = score

    # Return type with highest score, or "complex" if no match
    if type_scores:
        return max(type_scores, key=type_scores.get)
    return "complex"


def get_prompt_template(gen_type: str) -> str:
    """
    Get the prompt template for a specific generation type.

    Args:
        gen_type: The generation type key

    Returns:
        The prompt template string
    """
    return PROMPT_TEMPLATES.get(gen_type, COMPLEX_OBJECT_TEMPLATE)


def wrap_user_prompt(prompt: str, gen_type: Optional[str] = None) -> str:
    """
    Wrap the user prompt with appropriate context based on generation type.

    Args:
        prompt: The user's description of what they want to create
        gen_type: Optional generation type override. If None, auto-detected.

    Returns:
        The wrapped prompt with context
    """
    if gen_type is None:
        gen_type = detect_generation_type(prompt)

    template = get_prompt_template(gen_type)
    return template.format(description=prompt)


# =============================================================================
# API MESSAGE BUILDERS
# =============================================================================

def build_system_message() -> Dict[str, str]:
    """
    Build the system message for the API request.

    Returns:
        Dictionary with 'role' and 'content' keys
    """
    return {
        "role": "system",
        "content": SYSTEM_PROMPT,
    }


def build_user_message(prompt: str, gen_type: Optional[str] = None) -> Dict[str, str]:
    """
    Build the user message from a prompt, wrapped with appropriate context.

    Args:
        prompt: The user's description of what they want to create
        gen_type: Optional generation type override. If None, auto-detected.

    Returns:
        Dictionary with 'role' and 'content' keys
    """
    wrapped_prompt = wrap_user_prompt(prompt, gen_type)
    return {
        "role": "user",
        "content": wrapped_prompt,
    }


def build_messages(prompt: str, gen_type: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Build the complete list of messages for the API request.

    Args:
        prompt: The user's description of what they want to create
        gen_type: Optional generation type override. If None, auto-detected.

    Returns:
        List of message dictionaries for the chat completion API
    """
    return [
        build_system_message(),
        build_user_message(prompt, gen_type),
    ]


# =============================================================================
# RESPONSE PROCESSING
# =============================================================================

def extract_script_from_response(content: str) -> str:
    """
    Extract and clean the Python script from the API response.

    Handles cases where the response might include markdown code blocks,
    explanations, or other formatting.

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

    # Remove any explanatory text after the code
    # Look for common markers that indicate the end of code
    lines = script.split('\n')
    code_lines = []
    for line in lines:
        # Skip lines that look like explanations (start with certain words)
        stripped = line.strip()
        if stripped and not any(stripped.lower().startswith(prefix) for prefix in [
            'hope ', 'this ', 'here ', 'note:', 'explanation:', 'this script',
            'the above', 'remember', 'let me know', 'if you', 'you can'
        ]):
            code_lines.append(line)

    script = '\n'.join(code_lines).strip()

    # Ensure the script starts with a comment or import
    if script and not (script.startswith('#') or script.startswith('import')):
        # If it doesn't start with comment or import, check if there's code
        if 'import' in script or 'bpy' in script:
            # Find the first import or bpy line and use from there
            lines = script.split('\n')
            for i, line in enumerate(lines):
                if line.strip().startswith(('import', 'bpy', '#')):
                    script = '\n'.join(lines[i:])
                    break

    return script.strip()


def validate_script_format(script: str) -> tuple[bool, str]:
    """
    Validate that the extracted script appears to be valid Python.

    Args:
        script: The extracted Python script

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not script:
        return False, "Empty script received"

    # Check for basic Python structure
    if 'import bpy' not in script and 'bpy' not in script:
        return False, "Script does not appear to use Blender API (bpy)"

    # Try to compile the script to check syntax
    try:
        compile(script, '<string>', 'exec')
        return True, ""
    except SyntaxError as e:
        return False, f"Syntax error in generated script: {e}"


# =============================================================================
# EXAMPLE SCRIPTS - Reference implementations
# =============================================================================

EXAMPLE_SCRIPTS = {
    "red_cube": '''import bpy

# Create a red cube
bpy.ops.object.select_all(action='DESELECT')

# Create cube
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
cube = bpy.context.active_object
cube.name = "RedCube"

# Create red material
mat = bpy.data.materials.new(name="RedMaterial")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (1.0, 0.0, 0.0, 1.0)
bsdf.inputs["Roughness"].default_value = 0.5

# Assign material
cube.data.materials.append(mat)

# Ensure cube is selected and active
cube.select_set(True)
bpy.context.view_layer.objects.active = cube
''',
    "smooth_sphere": '''import bpy

# Create a smooth sphere with subdivision
bpy.ops.object.select_all(action='DESELECT')

# Create UV sphere with good base geometry
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0), segments=32, ring_count=16)
sphere = bpy.context.active_object
sphere.name = "SmoothSphere"

# Add subdivision surface modifier
mod = sphere.modifiers.new(name="Subdivision", type='SUBSURF')
mod.levels = 2
mod.render_levels = 3

# Shade smooth
bpy.ops.object.shade_smooth()

# Ensure sphere is selected and active
sphere.select_set(True)
bpy.context.view_layer.objects.active = sphere
''',
    "blue_cylinder": '''import bpy

# Create a blue metallic cylinder
bpy.ops.object.select_all(action='DESELECT')

# Create cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=(0, 0, 0), vertices=32)
cyl = bpy.context.active_object
cyl.name = "BlueCylinder"

# Create blue metallic material
mat = bpy.data.materials.new(name="BlueMetal")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.0, 0.3, 1.0, 1.0)
bsdf.inputs["Metallic"].default_value = 0.8
bsdf.inputs["Roughness"].default_value = 0.2

# Assign material
cyl.data.materials.append(mat)

# Ensure cylinder is selected and active
cyl.select_set(True)
bpy.context.view_layer.objects.active = cyl
''',
}


def get_example_script(example_name: str) -> Optional[str]:
    """
    Get an example script by name.

    Args:
        example_name: Name of the example script

    Returns:
        The example script string, or None if not found
    """
    return EXAMPLE_SCRIPTS.get(example_name)


def get_all_example_names() -> List[str]:
    """
    Get a list of all available example script names.

    Returns:
        List of example names
    """
    return list(EXAMPLE_SCRIPTS.keys())
