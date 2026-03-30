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
5. Objects must have DESCRIPTIVE, MEANINGFUL names based on what they represent (e.g., "RedCube", "SmoothSphere", "WoodenTable").
6. When creating MULTIPLE objects, give EACH object a UNIQUE, DESCRIPTIVE name (e.g., "ChairLeg_001", "ChairLeg_002", "ChairSeat").
7. ALWAYS deselect all objects before creating new ones: bpy.ops.object.select_all(action='DESELECT')
8. ALWAYS select the newly created object(s) and make them active at the end.
9. Handle errors gracefully - use try-except only when necessary.
10. When materials or colors are requested, create and assign them properly.
11. When modifiers are requested, add them with sensible default settings.
12. Ensure objects are linked to the current scene collection so they appear in the outliner.

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
- Rename: obj.name = "NewName" (use DESCRIPTIVE names, not generic like "Cube", "Sphere")
- Set location: obj.location = (x, y, z)
- Set rotation: obj.rotation_euler = (rx, ry, rz)  # in radians
- Set scale: obj.scale = (sx, sy, sz)
- Link to scene: bpy.context.collection.objects.link(obj) (ensures object appears in outliner)

NAMING CONVENTIONS (MANDATORY):
- Single primitive: Use descriptive name based on color/material + shape (e.g., "RedCube", "GoldSphere", "GlassCylinder")
- Multi-part objects: Use descriptive part names with suffixes (e.g., "TableTop", "TableLeg_001", "TableLeg_002")
- Objects with materials: Include material in name (e.g., "ChromeSphere", "WoodenChair")
- NEVER leave objects with default names like "Cube", "Sphere.001", "Mesh"
- Names should be in PascalCase or with underscores for readability

MATERIAL CREATION:
- Create material: mat = bpy.data.materials.new(name="MaterialName")
- Enable nodes: mat.use_nodes = True
- Assign to object: obj.data.materials.append(mat)
- Get BSDF node: bsdf = mat.node_tree.nodes["Principled BSDF"]
- Set base color: bsdf.inputs["Base Color"].default_value = (r, g, b, 1.0)  # RGB 0-1
- Set metallic: bsdf.inputs["Metallic"].default_value = 0.0-1.0
- Set roughness: bsdf.inputs["Roughness"].default_value = 0.0-1.0
- Set emission: bsdf.inputs["Emission"].default_value = (r, g, b, 1.0)
- Set transmission (glass): bsdf.inputs["Transmission"].default_value = 0.0-1.0
- Set IOR: bsdf.inputs["IOR"].default_value = 1.45

COMMON MATERIAL COLORS (RGB):
- Red: (1.0, 0.0, 0.0, 1.0)
- Green: (0.0, 1.0, 0.0, 1.0)
- Blue: (0.0, 0.0, 1.0, 1.0)
- Yellow: (1.0, 1.0, 0.0, 1.0)
- Orange: (1.0, 0.5, 0.0, 1.0)
- Purple: (0.5, 0.0, 1.0, 1.0)
- Pink: (1.0, 0.0, 1.0, 1.0)
- Cyan: (0.0, 1.0, 1.0, 1.0)
- White: (1.0, 1.0, 1.0, 1.0)
- Black: (0.0, 0.0, 0.0, 1.0)
- Gray: (0.5, 0.5, 0.5, 1.0)
- Brown: (0.4, 0.2, 0.0, 1.0)
- Gold: (1.0, 0.84, 0.0, 1.0)
- Silver: (0.75, 0.75, 0.75, 1.0)

MATERIAL TYPES:
- Matte/Diffuse: Metallic=0.0, Roughness=0.8-1.0
- Shiny/Glossy: Metallic=0.0, Roughness=0.1-0.3
- Metallic: Metallic=0.8-1.0, Roughness=0.2-0.4
- Mirror: Metallic=1.0, Roughness=0.0
- Glass: Transmission=0.9-1.0, Roughness=0.0-0.1, IOR=1.45
- Emissive/Glowing: Emission=(r, g, b, 1.0) with color values > 0

MODIFIER TYPES (obj.modifiers.new(name="Name", type='TYPE')):
- Subdivision Surface: type='SUBSURF', levels=2-3, render_levels=3-4
  - Use with shade_smooth() for best results
  - Start with enough base geometry for good smoothing
- Bevel: type='BEVEL', width=0.02-0.1, segments=2-6, limit_method='ANGLE'
  - For rounded edges on hard-surface models
- Array: type='ARRAY', count=3-5, relative_offset_displace=(1, 0, 0)
  - Creates copies in rows/columns
- Mirror: type='MIRROR', use_axis=(True, False, False)
  - Mirrors geometry across specified axis
- Boolean: type='BOOLEAN', operation='DIFFERENCE'/'UNION'/'INTERSECT'
  - Requires another object as boolean target
- Solidify: type='SOLIDIFY', thickness=0.01-0.1
  - Adds thickness to single-faced geometry
- Displace: type='DISPLACE', strength=0.1-1.0
  - Requires vertex groups for controlled displacement
- Smooth: type='SMOOTH', factor=1.0
  - Alternative to shade_smooth()
- Cast: type='CAST', cast_type='SPHERE'/'CYLINDER'/'CUBOID'
  - Deforms mesh into basic shapes
- Wave: type='WAVE'
  - Animated wave deformation

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

This involves creating materials. Follow these steps:
1. Create the mesh object first using bpy.ops.mesh.primitive_*_add()
2. Create a new material with bpy.data.materials.new(name="MaterialName")
3. Enable nodes: mat.use_nodes = True
4. Access the Principled BSDF node: bsdf = mat.node_tree.nodes["Principled BSDF"]
5. Set Base Color with RGBA tuple: bsdf.inputs["Base Color"].default_value = (r, g, b, 1.0)
6. Set other properties as needed (Metallic, Roughness, Emission, Transmission)
7. Assign the material to the object: obj.data.materials.append(mat)

For common colors (all RGB values 0.0-1.0):
- Red: (1.0, 0.0, 0.0, 1.0)
- Green: (0.0, 1.0, 0.0, 1.0)
- Blue: (0.0, 0.0, 1.0, 1.0)
- Yellow: (1.0, 1.0, 0.0, 1.0)
- Orange: (1.0, 0.5, 0.0, 1.0)
- Purple: (0.5, 0.0, 1.0, 1.0)
- Pink: (1.0, 0.0, 1.0, 1.0)
- Cyan: (0.0, 1.0, 1.0, 1.0)
- White: (1.0, 1.0, 1.0, 1.0)
- Black: (0.0, 0.0, 0.0, 1.0)
- Gold: (1.0, 0.84, 0.0, 1.0)
- Silver: (0.75, 0.75, 0.75, 1.0)

Material types:
- Shiny/Metallic: Metallic=0.8-1.0, Roughness=0.1-0.4
- Matte/Diffuse: Metallic=0.0, Roughness=0.7-1.0
- Glass: Transmission=0.9-1.0, Roughness=0.0-0.1, IOR=1.45
- Emissive/Glowing: Emission=(r, g, b, 1.0) with color values

Generate only the executable Python script."""

MODIFIER_GENERATION_TEMPLATE = """Create a Blender Python script that generates: {description}

This involves using modifiers. Follow these steps:
1. Create the base mesh object first using bpy.ops.mesh.primitive_*_add()
2. Add modifiers using: obj.modifiers.new(name="ModifierName", type='MODTYPE')
3. Configure modifier properties appropriately
4. For subdivision: type='SUBSURF', levels=2-3, then use bpy.ops.object.shade_smooth()
5. For bevel: type='BEVEL', width=0.02-0.1, segments=2-6
6. For array: type='ARRAY', count=3-5, relative_offset_displace=(1, 0, 0)
7. For mirror: type='MIRROR', use_axis=(True, False, False)
8. For solidify: type='SOLIDIFY', thickness=0.01-0.1

Common modifier workflow:
- Subdivision + Smooth: Creates smooth organic shapes
- Bevel: Rounds hard edges on mechanical objects
- Array + Object: Creates repeating patterns
- Mirror: Creates symmetrical objects efficiently

Generate only the executable Python script."""

COMPLEX_OBJECT_TEMPLATE = """Create a Blender Python script that generates: {description}

This is a complex object request. Ensure:
1. Build the object from appropriate primitives or create mesh data programmatically
2. For multi-part objects, create each part with UNIQUE, DESCRIPTIVE names (e.g., "Chair_Leg_001", "Table_Top", not "Cube.001")
3. Use collections or parenting if logical grouping is needed
4. Apply appropriate materials to each part
5. Position parts correctly relative to each other
6. Ensure all objects are linked to the current scene collection for outliner visibility

If creating detailed geometry:
- Use bpy.data.meshes.new() and bpy.data.objects.new() for manual mesh construction
- Define vertices, edges, faces for custom shapes
- Or combine primitives using boolean operations if appropriate

Generate only the executable Python script."""

MULTI_OBJECT_TEMPLATE = """Create a Blender Python script that generates: {description}

This request involves multiple objects. Ensure:
1. Create EACH object with a UNIQUE, DESCRIPTIVE name (not generic names like "Cube", "Sphere")
2. Examples of good names: "RedCube", "BlueSphere", "Leg_001", "Leg_002", "Seat_Cushion"
3. Position objects relative to each other appropriately
4. If the objects form a logical group, organize them appropriately
5. Each object should be selectable and manipulable independently (appears separately in outliner)
6. Leave ALL created objects selected at the end
7. Ensure all objects are linked to the current scene collection

For arrays or patterns:
- Use the Array modifier for repeated geometry, OR
- Create multiple objects in a loop with calculated positions and unique names (e.g., "Cube_001", "Cube_002")

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
    "material": [
        "red", "blue", "green", "yellow", "orange", "purple", "pink", "cyan", "white", "black", 
        "gray", "brown", "gold", "silver", "color", "material", "texture", "shiny", "metallic", 
        "matte", "rough", "emissive", "glowing", "glass", "transparent", "translucent", "mirror",
        "glossy", "diffuse", "shaded", "colored", "tinted"
    ],
    "modifier": [
        "smooth", "subdivision", "subsurf", "bevel", "rounded", "array", "mirror", 
        "duplicate", "solid", "thickness", "displace", "boolean", "solidify", "cast", 
        "wave", "curve", "lattice", "shrinkwrap", "wrap", "hook", "simpledeform",
        "bend", "twist", "taper", "stretch"
    ],
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

    # Priority ordering for when scores are equal or close
    # Material and modifier types should take precedence over primitive
    # because they represent more specific functionality
    priority_order = [
        "animation", "lighting", "camera",  # Scene setup first
        "material", "modifier",              # Object enhancement second
        "multi_object",                      # Count-based third
        "primitive",                         # Basic shapes last
        "complex",                           # Default fallback
    ]

    if type_scores:
        max_score = max(type_scores.values())
        # Get all types with max score
        top_types = [t for t, s in type_scores.items() if s == max_score]
        
        # If there's a tie, use priority ordering
        if len(top_types) > 1:
            for priority_type in priority_order:
                if priority_type in top_types:
                    return priority_type
        
        # Return type with highest score
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

# Create a red cube with proper naming
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

# Create a smooth sphere with proper naming
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

# Create a blue metallic cylinder with proper naming
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
    "red_sphere_subdivision": '''import bpy

# Create a red sphere with subdivision surface modifier
bpy.ops.object.select_all(action='DESELECT')

# Create UV sphere
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0), segments=32, ring_count=16)
sphere = bpy.context.active_object
sphere.name = "RedSmoothSphere"

# Add subdivision surface modifier for smoothness
mod = sphere.modifiers.new(name="Subdivision", type='SUBSURF')
mod.levels = 2
mod.render_levels = 3

# Create red material
mat = bpy.data.materials.new(name="RedMaterial")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (1.0, 0.0, 0.0, 1.0)
bsdf.inputs["Roughness"].default_value = 0.3

# Assign material to sphere
sphere.data.materials.append(mat)

# Apply smooth shading
bpy.ops.object.shade_smooth()

# Ensure sphere is selected and active
sphere.select_set(True)
bpy.context.view_layer.objects.active = sphere
''',
    "beveled_cube": '''import bpy

# Create a cube with bevel modifier for rounded edges
bpy.ops.object.select_all(action='DESELECT')

# Create cube
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
cube = bpy.context.active_object
cube.name = "BeveledCube"

# Add bevel modifier
bevel = cube.modifiers.new(name="Bevel", type='BEVEL')
bevel.width = 0.1
bevel.segments = 4
bevel.limit_method = 'ANGLE'

# Add subdivision for smoothness
subsurf = cube.modifiers.new(name="Subdivision", type='SUBSURF')
subsurf.levels = 1

# Apply smooth shading
bpy.ops.object.shade_smooth()

# Ensure cube is selected and active
cube.select_set(True)
bpy.context.view_layer.objects.active = cube
''',
    "gold_metallic_sphere": '''import bpy

# Create a shiny gold metallic sphere
bpy.ops.object.select_all(action='DESELECT')

# Create UV sphere
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0), segments=32, ring_count=16)
sphere = bpy.context.active_object
sphere.name = "GoldSphere"

# Add subdivision for smooth surface
mod = sphere.modifiers.new(name="Subdivision", type='SUBSURF')
mod.levels = 2
mod.render_levels = 3

# Create gold metallic material
mat = bpy.data.materials.new(name="GoldMaterial")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (1.0, 0.84, 0.0, 1.0)  # Gold color
bsdf.inputs["Metallic"].default_value = 1.0
bsdf.inputs["Roughness"].default_value = 0.2

# Assign material
sphere.data.materials.append(mat)

# Apply smooth shading
bpy.ops.object.shade_smooth()

# Ensure sphere is selected and active
sphere.select_set(True)
bpy.context.view_layer.objects.active = sphere
''',
    "glass_material_example": '''import bpy

# Create a glass sphere
bpy.ops.object.select_all(action='DESELECT')

# Create UV sphere with good geometry
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0), segments=32, ring_count=16)
sphere = bpy.context.active_object
sphere.name = "GlassSphere"

# Add subdivision for smooth surface
mod = sphere.modifiers.new(name="Subdivision", type='SUBSURF')
mod.levels = 2

# Create glass material
mat = bpy.data.materials.new(name="GlassMaterial")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (1.0, 1.0, 1.0, 1.0)
bsdf.inputs["Roughness"].default_value = 0.05
bsdf.inputs["Transmission"].default_value = 0.95
bsdf.inputs["IOR"].default_value = 1.45

# Assign material
sphere.data.materials.append(mat)

# Apply smooth shading
bpy.ops.object.shade_smooth()

# Ensure sphere is selected and active
sphere.select_set(True)
bpy.context.view_layer.objects.active = sphere
''',
    "array_modifier_example": '''import bpy

# Create a row of objects using array modifier
bpy.ops.object.select_all(action='DESELECT')

# Create base cube
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
cube = bpy.context.active_object
cube.name = "ArrayCube"

# Create green material
mat = bpy.data.materials.new(name="GreenMaterial")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.0, 0.8, 0.2, 1.0)
bsdf.inputs["Roughness"].default_value = 0.4
cube.data.materials.append(mat)

# Add array modifier to create 5 copies in a row
array_mod = cube.modifiers.new(name="Array", type='ARRAY')
array_mod.count = 5
array_mod.relative_offset_displace = (1.5, 0, 0)

# Ensure cube is selected and active
cube.select_set(True)
bpy.context.view_layer.objects.active = cube
''',
    "mirror_modifier_example": '''import bpy

# Create a symmetrical object using mirror modifier
bpy.ops.object.select_all(action='DESELECT')

# Create cube at positive X (will be mirrored)
bpy.ops.mesh.primitive_cube_add(size=1, location=(1, 0, 0))
cube = bpy.context.active_object
cube.name = "MirroredObject"

# Create blue material
mat = bpy.data.materials.new(name="BlueMaterial")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.0, 0.4, 1.0, 1.0)
bsdf.inputs["Roughness"].default_value = 0.3
cube.data.materials.append(mat)

# Add mirror modifier across X axis
mirror = cube.modifiers.new(name="Mirror", type='MIRROR')
mirror.use_axis = (True, False, False)
mirror.use_mirror_merge = True

# Ensure cube is selected and active
cube.select_set(True)
bpy.context.view_layer.objects.active = cube
''',
    "emissive_glowing_object": '''import bpy

# Create a glowing emissive object
bpy.ops.object.select_all(action='DESELECT')

# Create UV sphere
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0), segments=32, ring_count=16)
sphere = bpy.context.active_object
sphere.name = "GlowingSphere"

# Add subdivision
mod = sphere.modifiers.new(name="Subdivision", type='SUBSURF')
mod.levels = 1

# Create emissive glowing material
mat = bpy.data.materials.new(name="EmissiveMaterial")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.0, 0.0, 0.0, 1.0)
bsdf.inputs["Roughness"].default_value = 0.5
bsdf.inputs["Emission"].default_value = (0.0, 1.0, 1.0, 1.0)  # Cyan glow

# Assign material
sphere.data.materials.append(mat)

# Apply smooth shading
bpy.ops.object.shade_smooth()

# Ensure sphere is selected and active
sphere.select_set(True)
bpy.context.view_layer.objects.active = sphere
''',
    "multiple_cubes": '''import bpy

# Create multiple cubes in a row with descriptive names
bpy.ops.object.select_all(action='DESELECT')

created_objects = []
for i in range(3):
    # Create cube at calculated position
    x_pos = (i - 1) * 3  # Positions: -3, 0, 3
    bpy.ops.mesh.primitive_cube_add(size=1.5, location=(x_pos, 0, 0))
    cube = bpy.context.active_object
    
    # Assign descriptive unique name
    cube.name = f"Cube_{i+1:03d}"
    created_objects.append(cube)

# Select all created objects
for obj in created_objects:
    obj.select_set(True)
if created_objects:
    bpy.context.view_layer.objects.active = created_objects[-1]
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
