# SPDX-FileCopyrightText: 2025 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
AI Assistant - Panel Module

Defines the sidebar panel UI in the 3D Viewport N-panel under 'AI' category.
"""

import bpy
from bpy.types import Panel, PropertyGroup, UIList
from bpy.props import (
    StringProperty,
    IntProperty,
    BoolProperty,
    CollectionProperty,
)


class AIHistoryItem(PropertyGroup):
    """Represents a single entry in the generation history."""

    timestamp: StringProperty(
        name="Timestamp",
        description="When this generation occurred",
        default="",
    )

    prompt: StringProperty(
        name="Prompt",
        description="The user prompt that generated this script",
        default="",
    )

    script: StringProperty(
        name="Script",
        description="The generated Python script",
        default="",
    )

    executed: BoolProperty(
        name="Executed",
        description="Whether this script has been executed",
        default=False,
    )


class AI_UL_HistoryList(UIList):
    """UIList for displaying generation history items."""

    def draw_item(
        self,
        context,
        layout,
        data,
        item,
        icon,
        active_data,
        active_propname,
        index,
    ):
        # Compact display of history item
        row = layout.row(align=True)

        # Icon based on execution status
        icon_name = 'CHECKMARK' if item.executed else 'SCRIPT'
        row.label(icon=icon_name)

        # Timestamp and truncated prompt
        display_text = f"[{item.timestamp}] {item.prompt[:30]}"
        if len(item.prompt) > 30:
            display_text += "..."
        row.label(text=display_text)

        # Replay button
        op = row.operator(
            "ai.replay_generation",
            text="",
            icon='PLAY',
            emboss=False,
        )
        op.index = index


class AI_PT_AssistantPanel(Panel):
    """Main AI Assistant panel in the 3D Viewport N-panel."""

    bl_label = "AI Assistant"
    bl_idname = "AI_PT_AssistantPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AI'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        prefs = context.preferences.addons[__package__].preferences

        # Check API key status and show warning if missing
        if prefs.api_key_status != "Configured":
            box = layout.box()
            box.alert = True
            box.label(text="API Key Not Configured", icon='ERROR')
            box.label(
                text="Set OPENROUTER_API_KEY environment variable",
                icon='INFO',
            )
            layout.separator()

        # Prompt Input Section
        col = layout.column(align=True)
        col.label(text="Describe what you want to create:")
        col.prop(scene, "ai_prompt", text="")

        # Character count indicator
        char_count = len(scene.ai_prompt) if scene.ai_prompt else 0
        row = col.row()
        row.alignment = 'RIGHT'
        row.label(
            text=f"{char_count}/1000",
            icon='NONE',
        )
        if char_count > 1000:
            row.alert = True
            row.label(text="Too long!", icon='ERROR')

        layout.separator()

        # Generate Button
        row = layout.row()
        row.scale_y = 1.5
        row.operator(
            "ai.generate",
            text="Generate 3D Object",
            icon='OUTLINER_OB_MESH',
        )

        layout.separator()

        # Status Display
        box = layout.box()
        row = box.row()
        row.label(text="Status:", icon='INFO')
        row.label(text=scene.ai_status)

        # Show progress indicator if generating
        if scene.ai_is_generating:
            row = box.row()
            row.label(text="Generating...", icon='TIME')

        layout.separator()

        # Preview Section (if there's a script to preview)
        if scene.ai_current_script:
            box = layout.box()
            box.label(text="Generated Script Preview:", icon='SCRIPT')

            # Editable script text area
            col = box.column()
            col.prop(scene, "ai_preview_script", text="")
            col.label(text="Edit the script before execution if needed", icon='INFO')

            # Execute / Cancel buttons
            row = box.row(align=True)
            row.operator(
                "ai.execute_script",
                text="Execute Script",
                icon='PLAY',
            )
            row.operator(
                "ai.clear_preview",
                text="Cancel",
                icon='CANCEL',
            )

            layout.separator()

        # History Section
        layout.label(text="Generation History:", icon='HISTORY')

        if len(scene.ai_history) == 0:
            layout.label(text="No generations yet", icon='DOT')
        else:
            # History list
            layout.template_list(
                "AI_UL_HistoryList",
                "",
                scene,
                "ai_history",
                scene,
                "ai_history_index",
                rows=3,
                maxrows=6,
            )

            # Clear history button
            row = layout.row()
            row.operator(
                "ai.clear_history",
                text="Clear History",
                icon='TRASH',
            )


classes = (
    AIHistoryItem,
    AI_UL_HistoryList,
    AI_PT_AssistantPanel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # Scene properties for AI Assistant
    bpy.types.Scene.ai_prompt = StringProperty(
        name="AI Prompt",
        description="Enter a description of the 3D object you want to create",
        default="",
        maxlen=1000,
    )

    bpy.types.Scene.ai_status = StringProperty(
        name="AI Status",
        description="Current status of AI generation",
        default="Ready",
    )

    bpy.types.Scene.ai_is_generating = BoolProperty(
        name="Is Generating",
        description="Whether generation is currently in progress",
        default=False,
    )

    bpy.types.Scene.ai_current_script = StringProperty(
        name="Current Script",
        description="The currently generated script (before execution)",
        default="",
    )

    bpy.types.Scene.ai_preview_script = StringProperty(
        name="Preview Script",
        description="Editable preview of the generated Python script",
        default="",
    )

    bpy.types.Scene.ai_history = CollectionProperty(
        type=AIHistoryItem,
        name="AI History",
        description="History of AI generations",
    )

    bpy.types.Scene.ai_history_index = IntProperty(
        name="History Index",
        description="Index of selected history item",
        default=-1,
        min=-1,
    )


def unregister():
    # Remove scene properties
    del bpy.types.Scene.ai_history_index
    del bpy.types.Scene.ai_history
    del bpy.types.Scene.ai_preview_script
    del bpy.types.Scene.ai_current_script
    del bpy.types.Scene.ai_is_generating
    del bpy.types.Scene.ai_status
    del bpy.types.Scene.ai_prompt

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
