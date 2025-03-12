# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
import bpy
import bpy.utils.previews
import os
import json
import math
import mathutils

# --- Global Variables ---
keymaps = {}
_icons = None
ui_data = {'values': []}

# --- Utility Functions ---
def str_to_int(val):
    """Convert string to integer if possible, otherwise return 0"""
    return int(val) if val.isdigit() else 0

def str_to_icon(val):
    """Convert icon name to Blender internal icon value"""
    enum_items = bpy.types.UILayout.bl_rna.functions["prop"].parameters["icon"].enum_items
    if val in enum_items:
        return enum_items[val].value
    return str_to_int(val)

def check_prop(prop_path, glob, loc):
    """Safely check if a property exists using eval"""
    try:
        eval(prop_path, glob, loc)
        return True
    except Exception:
        return False

# --- Update Callback Functions ---
def update_colnum(self, context):
    _ = self.columnnumber
    bpy.ops.modset.autosave('INVOKE_DEFAULT')

def update_show_name(self, context):
    _ = self.showmodname
    bpy.ops.modset.autosave('INVOKE_DEFAULT')

def update_show_preset(self, context):
    _ = self.sna_show_preset
    bpy.ops.modset.autosave('INVOKE_DEFAULT')

def update_show_icon(self, context):
    _ = self.showmodicon
    bpy.ops.modset.autosave('INVOKE_DEFAULT')

def get_mod_icon(val):
    mapping = {
        'DATA_TRANSFER': 'MOD_DATA_TRANSFER',
        'MESH_CACHE': 'MOD_MESHDEFORM',
        'MESH_SEQUENCE_CACHE': 'MOD_MESHDEFORM',
        'NORMAL_EDIT': 'MOD_NORMALEDIT',
        'WEIGHTED_NORMAL': 'MOD_NORMALEDIT',
        'UV_PROJECT': 'MOD_UVPROJECT',
        'UV_WARP': 'MOD_UVPROJECT',
        'VERTEX_WEIGHT_EDIT': 'MOD_VERTEX_WEIGHT',
        'VERTEX_WEIGHT_MIX': 'MOD_VERTEX_WEIGHT',
        'VERTEX_WEIGHT_PROXIMITY': 'MOD_VERTEX_WEIGHT',
        'ARRAY': 'MOD_ARRAY',
        'BEVEL': 'MOD_BEVEL',
        'BOOLEAN': 'MOD_BOOLEAN',
        'BUILD': 'MOD_BUILD',
        'DECIMATE': 'MOD_DECIM',
        'EDGE_SPLIT': 'MOD_EDGESPLIT',
        'NODES': 'GEOMETRY_NODES',
        'MASK': 'MOD_MASK',
        'MIRROR': 'MOD_MIRROR',
        'MESH_TO_VOLUME': 'VOLUME_DATA',
        'MULTIRES': 'MOD_MULTIRES',
        'REMESH': 'MOD_REMESH',
        'SCREW': 'MOD_SCREW',
        'SKIN': 'MOD_SKIN',
        'SOLIDIFY': 'MOD_SOLIDIFY',
        'SUBSURF': 'MOD_SUBSURF',
        'TRIANGULATE': 'MOD_TRIANGULATE',
        'VOLUME_TO_MESH': 'VOLUME_DATA',
        'WELD': 'AUTOMERGE_OFF',
        'WIREFRAME': 'MOD_WIREFRAME',
        'ARMATURE': 'MOD_ARMATURE',
        'CAST': 'MOD_CAST',
        'CURVE': 'MOD_CURVE',
        'DISPLACE': 'MOD_DISPLACE',
        'HOOK': 'HOOK',
        'LAPLACIANDEFORM': 'MOD_MESHDEFORM',
        'LATTICE': 'MOD_LATTICE',
        'MESH_DEFORM': 'MOD_MESHDEFORM',
        'SHRINKWRAP': 'MOD_SHRINKWRAP',
        'SIMPLE_DEFORM': 'MOD_SIMPLEDEFORM',
        'SMOOTH': 'MOD_SMOOTH',
        'CORRECTIVE_SMOOTH': 'MOD_SMOOTH',
        'LAPLACIANSMOOTH': 'MOD_SMOOTH',
        'SURFACE_DEFORM': 'MOD_MESHDEFORM',
        'WARP': 'MOD_WARP',
        'WAVE': 'MOD_WAVE',
        'VOLUME_DISPLACE': 'VOLUME_DATA',
        'CLOTH': 'MOD_CLOTH',
        'COLLISION': 'MOD_PHYSICS',
        'DYNAMIC_PAINT': 'MOD_DYNAMICPAINT',
        'EXPLODE': 'MOD_EXPLODE',
        'FLUID': 'MOD_FLUIDSIM',
        'OCEAN': 'MOD_OCEAN',
        'PARTICLE_INSTANCE': 'MOD_PARTICLE_INSTANCE',
        'PARTICLE_SYSTEM': 'MOD_PARTICLES',
        'SOFT_BODY': 'MOD_SOFT',
        'SURFACE': 'OUTLINER_OB_SURFACE',
    }
    return mapping.get(val, '')

def add_to_ui_list(item):
    # Add parameters to ui_data['values']
    ui_data['values'].append([
        item.modname,
        item.modtype,
        item.modicon,
        item.modpath,
        item.aseetlib,
        item.parameters
    ])

def draw_add_button(layout_func):
    row = layout_func.row(align=True)
    row.scale_y = 1.8
    row.enabled = check_prop("bpy.context.object.modifiers.active.type", globals(), locals())
    row.active = check_prop("bpy.context.object.modifiers.active.type", globals(), locals())
    op = row.operator('modset.add_selected', text='Add Selected', icon_value=str_to_icon('ADD'), emboss=True)

def save_preset_json(preset_name):
    file_path = os.path.join(os.path.dirname(__file__), 'assets', 'prefs.json')
    template_vals = ui_data['values']
    prefs = bpy.context.scene.modset_prefs[0]
    pref_data = {
        "column_number": prefs.columnnumber,
        "show_mod_icon": prefs.showmodicon,
        "show_mod_name": prefs.showmodname,
        "show_preset": bpy.context.scene.sna_show_preset
    }
    
    keys = ["Name", "Type", "Icon", "Path", "AssetLibrary", "Parameters"]
    preset_data = [dict(zip(keys, vals)) for vals in template_vals]
    data = {preset_name: {"Preference": pref_data, "ModSet": preset_data}}
    try:
        with open(file_path, "r") as f:
            existing = json.load(f)
    except FileNotFoundError:
        existing = []
    existing.append(data)
    with open(file_path, "w") as f:
        json.dump(existing, f, indent=4)

def draw_edit_panel(layout_func):
    split = layout_func.split(factor=0.45, align=False)
    box = split.box()
    valid = (check_prop("bpy.context.scene.modset_preset", globals(), locals()) and
             len(bpy.context.scene.modset_preset) > bpy.context.scene.modset_active and
             bpy.context.scene.modset_active >= 0)
    box.enabled = valid
    box.active = valid

    col = box.column(align=True)
    row = col.row(align=True)
    if valid:
        op = row.operator(
            'modset.open_icon_picker',
            text='',
            icon_value=str_to_icon(bpy.context.scene.modset_preset[bpy.context.scene.modset_active].modicon),
            emboss=True
        )
        row.prop(bpy.context.scene.modset_preset[bpy.context.scene.modset_active], 'modname', text='', emboss=True)
        row2 = row.row(align=False)
        row2.alert = True
        op = row2.operator('modset.delete_active', text='', icon_value=str_to_icon('TRASH'), emboss=True)
        op.collection_index = 0
    else:
        blank = row.row(align=True)
        blank.enabled = False
        blank.label(text='', icon_value=1)
        bbox = blank.box()
        bbox.enabled = False
        bbox.label(text=' ', icon_value=0)
        row.separator(factor=0.2)
        row.operator('sn.dummy_button_operator', text='', icon_value=21, emboss=True)
    col.separator(factor=0.6)
    split2 = col.split(factor=0.25, align=False)
    split2.separator(factor=0.0)
    split3 = split2.split(factor=0.666, align=False)
    split3.enabled = (bpy.context.scene.modset_active >= bpy.context.scene.modset_prefs[0].columnnumber)
    op = split3.operator('modset.move_button', text='', icon_value=str_to_icon('SORT_DESC'), emboss=True)
    op.s_amount = int(bpy.context.scene.modset_prefs[0].columnnumber * -1)
    split3.separator(factor=0.0)
    row_move = col.row(align=True)
    split4 = row_move.split(factor=0.1, align=True)
    split4.enabled = (bpy.context.scene.modset_active > 0)
    split4.separator(factor=0.0)
    op = split4.operator('modset.move_button', text='', icon_value=str_to_icon('BACK'), emboss=True)
    op.s_amount = -1
    split5 = row_move.split(factor=0.9, align=True)
    split5.enabled = (bpy.context.scene.modset_active < len(bpy.context.scene.modset_preset) - 1)
    op = split5.operator('modset.move_button', text='', icon_value=str_to_icon('FORWARD'), emboss=True)
    op.s_amount = 1
    split5.separator(factor=0.0)
    split6 = col.split(factor=0.25, align=False)
    split6.separator(factor=0.0)
    split7 = split6.split(factor=0.666, align=False)
    split7.enabled = (bpy.context.scene.modset_active < len(bpy.context.scene.modset_preset) - bpy.context.scene.modset_prefs[0].columnnumber)
    op = split7.operator('modset.move_button', text='', icon_value=str_to_icon('SORT_ASC'), emboss=True)
    op.s_amount = bpy.context.scene.modset_prefs[0].columnnumber
    split7.separator(factor=0.0)
    col2 = split.column(align=True)
    col2.separator(factor=0.8)
    
    # Column number setting
    split_prop = col2.split(factor=0.24, align=True)
    split_prop.prop(bpy.context.scene.modset_prefs[0], 'columnnumber', text='', icon_value=0, emboss=True)
    split_prop.label(text='Column', icon_value=0)
    

    row_buttons = col2.row(align=True)
    
    # Icon button
    icon_btn = row_buttons.row(align=True)
    icon_btn.prop(
        bpy.context.scene.modset_prefs[0], 'showmodicon',
        text="Icon",
        icon='HIDE_OFF' if bpy.context.scene.modset_prefs[0].showmodicon else 'HIDE_ON',
        emboss=True,
        toggle=True
    )
    icon_btn.active = bpy.context.scene.modset_prefs[0].showmodicon
    
    # Name button
    name_btn = row_buttons.row(align=True)
    name_btn.prop(
        bpy.context.scene.modset_prefs[0], 'showmodname',
        text="Name",
        icon='HIDE_OFF' if bpy.context.scene.modset_prefs[0].showmodname else 'HIDE_ON',
        emboss=True,
        toggle=True
    )
    name_btn.active = bpy.context.scene.modset_prefs[0].showmodname
    
    col2.operator('modset.load_preset', text='Load from Prefs', icon_value=str_to_icon('FILE_REFRESH'), emboss=True)
    
    delete_row = col2.row()
    delete_row.alert = True
    delete_row.operator('modset.delete_all', text='Delete all ModSet', icon_value=str_to_icon('TRASH'), emboss=True)


def get_modifier_parameters(mod):
    """Extract parameters from a modifier that can be saved and restored later"""
    ignore_props = {
        "show_viewport", "show_render", "show_in_editmode", "show_on_cage",
        "is_active", "show_expanded", "use_pin_to_last", "use_apply_on_spline"
    }
    
    # Internal properties to ignore for Hook modifiers
    hook_internal_props = {"matrix_inverse", "center", "matrix"}
    
    params = {}
    for prop in mod.bl_rna.properties:
        if prop.is_readonly:
            continue
        if prop.identifier in {'name', 'type', 'rna_type'} or prop.identifier in ignore_props:
            continue
        if mod.type == 'HOOK' and prop.identifier in hook_internal_props:
            continue
        
        try:
            value = getattr(mod, prop.identifier)
            
            # Special handling for collection references (Boolean modifier etc.)
            if prop.type == 'POINTER' and prop.identifier == 'collection' and value:
                if hasattr(value, "name"):
                    params['collection_name'] = value.name  # Save collection name
                continue
            # Ignore other object references
            elif prop.type == 'POINTER':
                continue
                
            # Process array properties
            if getattr(prop, 'array_length', 0) > 0:
                if prop.type == 'BOOLEAN':
                    params[prop.identifier] = [bool(v) for v in value]
                else:
                    params[prop.identifier] = list(value)
            # Process collection properties (save as name list)
            elif prop.type == 'COLLECTION' and value:
                names = [item.name for item in value if hasattr(item, "name")]
                if names:  # Don't save empty lists
                    params[prop.identifier] = names
            # Save basic data types only
            elif isinstance(value, (int, float, bool, str)):
                params[prop.identifier] = value
            # Process set types
            elif isinstance(value, (set, frozenset)):
                params[prop.identifier] = list(value)
        except Exception as e:
            print(f"Error processing {prop.identifier}: {str(e)}")
    return params

def restore_parameters(mod, params):
    if 'collection_name' in params and hasattr(mod, 'collection'):
        collection_name = params.pop('collection_name')
        collection = bpy.data.collections.get(collection_name)
        if collection:
            mod.collection = collection
            print(f"Restored collection reference: {collection_name}")
        else:
            print(f"Warning: Collection {collection_name} not found")
    
    for key, value in params.items():
        prop = mod.bl_rna.properties.get(key)
        if not prop:
            continue

        if prop.type == 'COLLECTION' and isinstance(value, list) and all(isinstance(item, str) for item in value):
            try:
                # Clear existing collection
                if hasattr(getattr(mod, key), "clear"):
                    getattr(mod, key).clear()
                
                # Add collection items from name list
                coll = getattr(mod, key)
                for name in value:
                    if hasattr(coll, "add"):
                        item = coll.add()
                        if hasattr(item, "name"):
                            item.name = name
            except Exception as e:
                print(f"Collection restoration error [{key}]: {str(e)}")
            continue

        # Process array properties
        elif getattr(prop, 'array_length', 0) > 0:
            try:
                setattr(mod, key, tuple(value))
            except Exception as e:
                print(f"Array restoration error [{key}]: {str(e)}")
        # Process enum flags
        elif prop.is_enum_flag:
            try:
                set_value = {item for item in value if item in prop.enum_items}
                setattr(mod, key, set_value)
            except Exception as e:
                print(f"Enum setting error [{key}]: {str(e)}")
        # Process basic types
        else:
            try:
                setattr(mod, key, value)
            except Exception as e:
                print(f"Property assignment error [{key}]: {str(e)}")

def safe_serialize(value):
    """Convert any Blender data type to a safe JSON format"""
    # Process mathutils objects like Vector
    if hasattr(value, "to_list"):
        return value.to_list()
    # Process IDPropertyArray
    elif hasattr(value, "__class__") and value.__class__.__name__ == 'IDPropertyArray':
        return list(value)
    # Process list/tuple types (recursively process internal elements)
    elif isinstance(value, (list, tuple)):
        return [safe_serialize(item) for item in value]
    # Process dictionary types (recursively process internal elements)
    elif isinstance(value, dict):
        return {k: safe_serialize(v) for k, v in value.items()}
    # Process set types
    elif isinstance(value, (set, frozenset)):
        return [safe_serialize(item) for item in value]
    # Basic types are returned as is
    elif isinstance(value, (int, float, bool, str, type(None))):
        return value
    # Other types are ignored (option to return string representation also exists)
    else:
        print(f"Unsupported type: {type(value).__name__}")
        return None

def get_geometry_nodes_parameters(mod):
    params = {}
    if not mod.node_group:
        return params

    for prop_name in mod.keys():
        if prop_name.startswith(('Input_', 'Socket_')) and not prop_name.endswith(('_use_attribute', '_attribute_name')):
            try:
                value = mod[prop_name]
                
                # Process collection references as name
                if hasattr(value, "bl_rna") and value.bl_rna.identifier == 'Collection':
                    params[prop_name] = value.name
                    continue
                
                # Ignore object references
                if isinstance(value, bpy.types.Object):
                    continue
                
                # Process special types
                if hasattr(value, "to_list"):
                    params[prop_name] = value.to_list()
                elif hasattr(value, "__class__") and value.__class__.__name__ == 'IDPropertyArray':
                    params[prop_name] = list(value)
                    # Basic data types
                elif isinstance(value, (int, float, bool, str, list, tuple)):
                    params[prop_name] = safe_serialize(value)
                
            except Exception as e:
                print(f"Parameter extraction error [{prop_name}]: {str(e)}")
    
    return params

def register():
    global _icons
    _icons = bpy.utils.previews.new()

def unregister():
    global _icons
    bpy.utils.previews.remove(_icons)