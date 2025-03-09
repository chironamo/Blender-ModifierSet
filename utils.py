#以下はutils.py
import bpy
import bpy.utils.previews
import os
import json
import math

# --- グローバル変数 ---
keymaps = {}
_icons = None
ui_data = {'values': []}

# --- ユーティリティ関数 ---
def str_to_int(val):
    return int(val) if val.isdigit() else 0

def str_to_icon(val):
    enum_items = bpy.types.UILayout.bl_rna.functions["prop"].parameters["icon"].enum_items
    if val in enum_items:
        return enum_items[val].value
    return str_to_int(val)

def check_prop(prop_path, glob, loc):
    try:
        eval(prop_path, glob, loc)
        return True
    except Exception:
        return False

# --- Update Callback 関数 ---
def update_colnum(self, context):
    _ = self.columnnumber
    bpy.ops.modset.autosave('INVOKE_DEFAULT')

def update_show_name(self, context):
    _ = self.showmodname
    bpy.ops.modset.autosave('INVOKE_DEFAULT')

def update_show_preset(self, context):
    _ = self.sna_show_preset
    bpy.ops.modset.autosave('INVOKE_DEFAULT')

def update_show_add(self, context):
    _ = self.showaddalways
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
    # ui_data['values'] に、Parameters項目も追加する
    ui_data['values'].append([
        item.modname,
        item.modtype,
        item.modicon,
        item.modpath,
        item.aseetlib,
        item.parameters
    ])

def draw_add_button(layout_func):
    col = layout_func.column()
    col.enabled = check_prop("bpy.context.object.modifiers.active.type", globals(), locals())
    col.active = check_prop("bpy.context.object.modifiers.active.type", globals(), locals())
    col.operator('modset.add_selected', text='Add Selected', icon_value=str_to_icon('ADD'), emboss=True)

def save_preset_json(preset_name):
    file_path = os.path.join(os.path.dirname(__file__), 'assets', 'prefs.json')
    template_vals = ui_data['values']
    prefs = bpy.context.scene.modset_prefs[0]
    pref_data = {
        "column_number": prefs.columnnumber,
        "show_mod_icon": prefs.showmodicon,
        "show_mod_name": prefs.showmodname,
        "show_add_always": prefs.showaddalways,
        "show_preset": bpy.context.scene.sna_show_preset
    }
    # キーリストに Parameters を追加
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
    split_prop = col2.split(factor=0.24, align=True)
    split_prop.prop(bpy.context.scene.modset_prefs[0], 'columnnumber', text='', icon_value=0, emboss=True)
    split_prop.label(text='Column', icon_value=0)
    col2.prop(bpy.context.scene.modset_prefs[0], 'showmodicon', text='Show Icon', icon_value=0, emboss=True)
    col2.prop(bpy.context.scene.modset_prefs[0], 'showmodname', text='Show Name', icon_value=0, emboss=True)
    col2.prop(bpy.context.scene.modset_prefs[0], 'showaddalways', text='Show [+Add] always', icon_value=0, emboss=True)
    col2.operator('modset.delete_all', text='Delete all ModSet', icon_value=str_to_icon('TRASH'), emboss=True)
    col2.operator('modset.load_preset', text='Load from Prefs', icon_value=str_to_icon('FILE_REFRESH'), emboss=True)

def get_modifier_parameters(mod):
    """
    指定したモディファイアのパラメーターを取得します。
    数値、文字列、真偽値はそのまま保存し、
    Vector（iterable）の場合はリストに変換して保存します。
    さらに、setやfrozensetなども対応するようにします。
    """
    import mathutils
    ignore_props = {
         "show_viewport", "show_render", "show_in_editmode", "show_on_cage",
         "is_active", "show_expanded", "use_pin_to_last", "use_apply_on_spline"
    }
    params = {}
    for prop in mod.bl_rna.properties:
        if prop.is_readonly:
            continue
        if prop.identifier in {'name', 'type', 'rna_type'} or prop.identifier in ignore_props:
            continue

        try:
            value = getattr(mod, prop.identifier)
            # 明示的に Vector 型のプロパティの場合は list 化
            if prop.identifier in {"relative_offset_displace", "constant_offset_displace"}:
                params[prop.identifier] = list(value)
            elif isinstance(value, (int, float, bool, str)):
                params[prop.identifier] = value
            # set, frozenset も list に変換して保存
            elif isinstance(value, (set, frozenset)):
                params[prop.identifier] = list(value)
            # 文字列はイテラブルであるため除外
            elif hasattr(value, "__iter__") and not isinstance(value, str):
                try:
                    # 全て float 変換できれば float のリストに
                    converted = [float(v) for v in value]
                    params[prop.identifier] = converted
                except Exception:
                    # できなければそのまま list に変換
                    params[prop.identifier] = list(value)
        except Exception:
            pass
    return params

def get_geometry_nodes_parameters(mod):
    """ジオメトリーノードモディファイアのパラメーターを取得（コンパクトJSON対応版）"""
    params = {}
    if not mod.node_group:
        return params

    # プロパティを直接走査
    for prop_name in mod.keys():
        if prop_name.startswith(('Input_', 'Socket_')) and not prop_name.endswith(('_use_attribute', '_attribute_name')):
            try:
                value = mod[prop_name]
                # 型に応じた簡潔な変換
                if isinstance(value, (float, int)):
                    params[prop_name] = round(value, 4) if isinstance(value, float) else value
                else:
                    params[prop_name] = value
            except Exception as e:
                print(f"パラメーター取得エラー [{prop_name}]: {str(e)}")
    
    return params

def register():
    global _icons
    _icons = bpy.utils.previews.new()

def unregister():
    global _icons
    bpy.utils.previews.remove(_icons)