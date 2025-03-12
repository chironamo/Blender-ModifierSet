import bpy
from . import utils

# Draw the main ModSet panel in the modifier tab of the Properties editor
# This function is registered to be called when the modifier panel is drawn
def draw_mod_panel(self, context):
    scene = bpy.context.scene
    layout = self.layout
    box = layout.box()
    row = box.row(align=True)
    
    # Draw expand/collapse arrow button with appropriate icon
    op = row.operator(
        'modset.expand_panel',
        text='',
        icon_value=utils.str_to_icon('DOWNARROW_HLT') if scene.modset_isexpand else utils.str_to_icon('RIGHTARROW'),
        emboss=False
    )
    
    # Panel header with title and settings button
    row.label(text='Modifier Set', icon_value=0)
    row.operator('modset.toggle_setting', text='',
                 icon_value=utils.str_to_icon('SETTINGS'),
                 emboss=True, depress=scene.modset_setting)

    # Only draw the main panel content if expanded
    if scene.modset_isexpand:
        col = box.column()
        
        # Create a grid layout based on user preferences
        grid = col.grid_flow(
            columns=bpy.context.scene.modset_prefs[0].columnnumber,
            row_major=True, even_columns=True, even_rows=True, align=True
        )
        
        # Settings mode - draw buttons that can be selected/edited
        if scene.modset_setting:
            for i, mod in enumerate(scene.modset_preset):
                op = grid.operator(
                    'modset.set_active_button',
                    text=mod.modname if bpy.context.scene.modset_prefs[0].showmodname else '',
                    icon_value=(utils.str_to_icon(mod.modicon)
                                if bpy.context.scene.modset_prefs[0].showmodicon else utils.str_to_icon('NONE')),
                    emboss=True,
                    depress=(i == scene.modset_active)
                )
                op.collection_index = i
        # Normal mode - draw buttons that apply modifiers when clicked
        else:
            for i, mod in enumerate(scene.modset_preset):
                op = grid.operator(
                    'modset.user_button',
                    text=mod.modname if bpy.context.scene.modset_prefs[0].showmodname else '',
                    icon_value=(utils.str_to_icon(mod.modicon)
                                if bpy.context.scene.modset_prefs[0].showmodicon else utils.str_to_icon('NONE')),
                    emboss=True
                )
                op.collection_index = i

        # Add empty spaces to maintain grid layout if needed
        colnum = bpy.context.scene.modset_prefs[0].columnnumber
        rem = len(scene.modset_preset) % colnum
        if rem:
            for _ in range(colnum - rem):
                grid.separator(factor=1.0)

        # Draw additional UI elements in settings mode
        if scene.modset_setting:
            utils.draw_add_button(col)
            utils.draw_edit_panel(col)

# Icon picker panel for selecting custom icons
class MODSET_IconPanel(bpy.types.Panel):
    bl_label = 'New Panel'
    bl_idname = 'modset.icon_panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_context = ''
    bl_order = 0
    bl_ui_units_x = 20

    def draw_header(self, context):
        pass

    # Draw a grid of all available Blender icons for selection
    def draw(self, context):
        layout = self.layout
        grid = layout.grid_flow(columns=20, row_major=True, even_columns=True, even_rows=True, align=True)
        
        # Get all available icons from Blender's internal icon set
        icons = list(bpy.types.UILayout.bl_rna.functions["prop"].parameters["icon"].enum_items.values())
        for item in icons:
            op = grid.operator('modset.select_icon', text='', icon_value=utils.str_to_icon(item.identifier), emboss=True)
            op.s_icon = item.identifier

classes = [
    MODSET_IconPanel,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.DATA_PT_modifiers.append(draw_mod_panel)

def unregister():
    bpy.types.DATA_PT_modifiers.remove(draw_mod_panel)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
