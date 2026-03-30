# SPDX-FileCopyrightText: 2025 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "AI Assistant",
    "author": "Blender Foundation",
    "version": (1, 0, 0),
    "blender": (5, 0, 0),
    "location": "View3D > N-Panel > AI",
    "description": "AI-powered text-to-3D generation using OpenRouter API",
    "warning": "",
    "doc_url": "",
    "support": 'OFFICIAL',
    "category": "3D View",
}

import bpy
from bpy.props import StringProperty, IntProperty, EnumProperty
from bpy.types import AddonPreferences

from . import api_client
from . import operators
from . import panel
from . import prompts


class AIAddonPreferences(AddonPreferences):
    bl_idname = __name__

    model: EnumProperty(
        name="AI Model",
        description="Select the AI model for text-to-3D generation",
        items=[
            ('anthropic/claude-sonnet-4.6', 'Claude Sonnet 4.6', 'Anthropic Claude Sonnet 4.6'),
            ('openai/gpt-4o', 'GPT-4o', 'OpenAI GPT-4o'),
        ],
        default='anthropic/claude-sonnet-4.6',
    )

    timeout: IntProperty(
        name="API Timeout",
        description="Timeout for API calls in seconds",
        default=30,
        min=10,
        max=120,
    )

    api_key_status: StringProperty(
        name="API Key Status",
        description="Status of OpenRouter API key",
        default="Not configured",
    )

    def draw(self, context):
        layout = self.layout

        # Check for API key in environment
        import os
        api_key = os.environ.get('OPENROUTER_API_KEY', '')
        if api_key:
            self.api_key_status = "Configured"
            row = layout.row()
            row.label(text="API Key: Configured", icon='CHECKMARK')
        else:
            self.api_key_status = "Not configured"
            row = layout.row()
            row.label(text="API Key: Not configured", icon='ERROR')
            row = layout.row()
            row.label(text="Set OPENROUTER_API_KEY environment variable", icon='INFO')

        layout.separator()
        layout.prop(self, "model")
        layout.prop(self, "timeout")


classes = [
    AIAddonPreferences,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    panel.register()
    operators.register()


def unregister():
    operators.unregister()
    panel.unregister()

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
