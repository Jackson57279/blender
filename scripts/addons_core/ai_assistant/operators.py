# SPDX-FileCopyrightText: 2025 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
AI Assistant - Operators Module

Defines operators for AI generation, script execution, history management, and more.
"""

import bpy
import time
from bpy.types import Operator

from . import api_client
from . import prompts


class AI_OT_Generate(Operator):
    """Generate a 3D object from the current prompt using AI."""

    bl_idname = "ai.generate"
    bl_label = "Generate 3D Object"
    bl_description = "Generate a 3D object from the prompt using AI"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # Check if prompt is not empty and not too long
        prompt = context.scene.ai_prompt
        return bool(prompt and len(prompt) <= 1000)

    def execute(self, context):
        scene = context.scene
        prefs = context.preferences.addons[__package__].preferences

        # Check API key is configured
        if prefs.api_key_status != "Configured":
            self.report({'ERROR'}, "OpenRouter API key not configured. Set OPENROUTER_API_KEY environment variable.")
            scene.ai_status = "Error: API key not configured"
            return {'CANCELLED'}

        # Set generating state
        scene.ai_is_generating = True
        scene.ai_status = "Generating..."

        # Create API client with user preferences
        client = api_client.create_client(timeout=prefs.timeout)

        # Build the messages for the API request
        messages = prompts.build_messages(scene.ai_prompt)

        # Make the API call
        response = client.chat_completion(
            messages=messages,
            model=prefs.model,
        )

        # Handle the response
        if response.success:
            # Extract the generated script from the response
            generated_script = response.content

            # Store the script in preview
            scene.ai_current_script = generated_script

            # Add to history
            self._add_to_history(context, scene.ai_prompt, generated_script)

            # Complete
            scene.ai_is_generating = False
            scene.ai_status = "Generation complete. Review and execute the script."

            self.report({'INFO'}, "Script generated. Review and click Execute.")
            return {'FINISHED'}
        else:
            # Handle error
            scene.ai_is_generating = False
            error_message = api_client.get_user_friendly_error_message(response)
            scene.ai_status = f"Error: {error_message}"
            self.report({'ERROR'}, error_message)
            return {'CANCELLED'}

    def _add_to_history(self, context, prompt, script):
        """Add a generation to history."""
        scene = context.scene
        history_item = scene.ai_history.add()
        history_item.timestamp = time.strftime("%H:%M:%S")
        history_item.prompt = prompt
        history_item.script = script
        history_item.executed = False


class AI_OT_ExecuteScript(Operator):
    """Execute the generated Python script in Blender."""

    bl_idname = "ai.execute_script"
    bl_label = "Execute Script"
    bl_description = "Execute the generated Python script"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return bool(context.scene.ai_current_script)

    def execute(self, context):
        scene = context.scene
        script = scene.ai_current_script

        # Push undo state
        bpy.ops.ed.undo_push(message="Execute AI Generated Script")

        try:
            # Execute the script
            exec(script, {"__name__": "__main__", "bpy": bpy, "mathutils": __import__('mathutils')})

            # Mark as executed in history
            if scene.ai_history:
                scene.ai_history[-1].executed = True

            # Clear preview
            scene.ai_current_script = ""
            scene.ai_status = "Script executed successfully"

            self.report({'INFO'}, "Script executed successfully!")
            return {'FINISHED'}

        except Exception as e:
            scene.ai_status = f"Execution error: {str(e)}"
            self.report({'ERROR'}, f"Script execution failed: {str(e)}")
            return {'CANCELLED'}


class AI_OT_ReplayGeneration(Operator):
    """Replay a previous generation from history."""

    bl_idname = "ai.replay_generation"
    bl_label = "Replay Generation"
    bl_description = "Re-execute a script from history"
    bl_options = {'REGISTER', 'UNDO'}

    index: bpy.props.IntProperty(
        name="History Index",
        description="Index of the history item to replay",
        default=0,
        min=0,
    )

    @classmethod
    def poll(cls, context):
        return len(context.scene.ai_history) > 0

    def execute(self, context):
        scene = context.scene

        # Validate index
        if self.index < 0 or self.index >= len(scene.ai_history):
            self.report({'ERROR'}, "Invalid history index")
            return {'CANCELLED'}

        history_item = scene.ai_history[self.index]
        script = history_item.script

        # Push undo state
        bpy.ops.ed.undo_push(message="Replay AI Generation")

        try:
            # Execute the script
            exec(script, {"__name__": "__main__", "bpy": bpy, "mathutils": __import__('mathutils')})

            scene.ai_status = f"Replayed: {history_item.prompt}"
            self.report({'INFO'}, f"Replayed generation: {history_item.prompt}")
            return {'FINISHED'}

        except Exception as e:
            scene.ai_status = f"Replay error: {str(e)}"
            self.report({'ERROR'}, f"Replay failed: {str(e)}")
            return {'CANCELLED'}


class AI_OT_ClearPreview(Operator):
    """Clear the current script preview without executing."""

    bl_idname = "ai.clear_preview"
    bl_label = "Clear Preview"
    bl_description = "Clear the script preview without executing"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return bool(context.scene.ai_current_script)

    def execute(self, context):
        scene = context.scene
        scene.ai_current_script = ""
        scene.ai_status = "Preview cleared"
        self.report({'INFO'}, "Preview cleared")
        return {'FINISHED'}


class AI_OT_ClearHistory(Operator):
    """Clear all history entries."""

    bl_idname = "ai.clear_history"
    bl_label = "Clear History"
    bl_description = "Clear all generation history"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return len(context.scene.ai_history) > 0

    def execute(self, context):
        scene = context.scene
        scene.ai_history.clear()
        scene.ai_history_index = -1
        scene.ai_status = "History cleared"
        self.report({'INFO'}, "History cleared")
        return {'FINISHED'}


classes = (
    AI_OT_Generate,
    AI_OT_ExecuteScript,
    AI_OT_ReplayGeneration,
    AI_OT_ClearPreview,
    AI_OT_ClearHistory,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
