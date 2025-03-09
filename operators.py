#以下はoperators.py
import bpy
import os
import json
from . import utils

# --- アドオン設定 ---
class MODSET_AddonPrefs(bpy.types.AddonPreferences):
    bl_idname = __package__

    def draw(self, context):
        layout = self.layout
        split = layout.split(factor=0.12842649221420288, align=False)
        split.label(text='Prefs file :', icon_value=0)
        split_path = split.split(factor=0.8119289875030518, align=False)
        split_path.label(text=os.path.join(os.path.dirname(__file__), 'assets', 'prefs.json'), icon_value=0)
        split_path.operator('modset.open_prefs_folder', text='Open Folder', icon_value=0, emboss=True)

class MODSET_OpenPrefsFolder(bpy.types.Operator):
    bl_idname = "modset.open_prefs_folder"
    bl_label = "Open Prefs Folder"
    bl_description = "Open directory containing prefs file"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        import subprocess
        import platform
        folder_path = os.path.join(os.path.dirname(__file__), 'assets')
        
        # OSごとのフォルダ開き方
        if platform.system() == "Windows":
            subprocess.Popen(f'explorer "{folder_path}"')
        elif platform.system() == "Darwin":
            subprocess.Popen(['open', folder_path])
        else:
            subprocess.Popen(['xdg-open', folder_path])
            
        return {"FINISHED"}

# --- オペレーター ---
class MODSET_ExpandPanel(bpy.types.Operator):
    bl_idname = "modset.expand_panel"
    bl_label = "Expand Panel"
    bl_description = "Expand ModSet panel"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = bpy.context.scene
        scene.modset_isexpand = not scene.modset_isexpand
        if scene.modset_isexpand:
            bpy.ops.modset.load_preset('INVOKE_DEFAULT')
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

class MODSET_ToggleSetting(bpy.types.Operator):
    bl_idname = "modset.toggle_setting"
    bl_label = "Toggle Setting"
    bl_description = "Setting mode toggle"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        bpy.context.scene.modset_setting = not bpy.context.scene.modset_setting
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

class MODSET_UserButton(bpy.types.Operator):
    bl_idname = "modset.user_button"
    bl_label = "User Button"
    bl_description = "Add Modifier to Selected Object"
    bl_options = {"REGISTER", "UNDO"}
    collection_index: bpy.props.IntProperty(name='collection index', default=0)

    def execute(self, context):
        import mathutils
        scene = bpy.context.scene
        preset = scene.modset_preset[self.collection_index]
        
        # ノードグループによるモディファイヤー追加の場合
        if preset.modpath != '':
            if preset.aseetlib == '':
                bpy.ops.object.modifier_add_node_group(
                    'INVOKE_DEFAULT',
                    asset_library_type='ESSENTIALS',
                    asset_library_identifier='',
                    relative_asset_identifier=preset.modpath
                )
            else:
                bpy.ops.object.modifier_add_node_group(
                    'INVOKE_DEFAULT',
                    asset_library_type='CUSTOM',
                    asset_library_identifier=preset.aseetlib,
                    relative_asset_identifier=preset.modpath
                )
        # 通常のモディファイヤー追加の場合
        else:
            bpy.ops.object.modifier_add('INVOKE_DEFAULT', type=preset.modtype)
        
        new_mod = bpy.context.object.modifiers.active
        
        # 保存されたパラメーターがあれば復元する
        if preset.parameters != "":
            try:
                params = json.loads(preset.parameters)
                print(f"適用パラメーター: {params}")
                
                # 通常モディファイヤー用のパラメーター復元処理
                if preset.modpath == '':  # 通常モディファイヤーの場合
                    from .utils import restore_parameters
                    restore_parameters(new_mod, params)
                
                # ジオメトリーノード用のパラメーター復元処理（既存の処理を維持）
                else:  
                    for key, value in params.items():
                        try:
                            if isinstance(value, (mathutils.Vector, list, tuple)):
                                converted = [round(float(v), 4) for v in value]
                            elif isinstance(value, str) and value.startswith("OBJ:"):
                                obj = bpy.data.objects.get(value[4:])
                            else:
                                new_mod[key] = value
                            print(f"ジオメトリーノード設定成功: {key} = {value}")
                        except Exception as e:
                            print(f"ジオメトリーノード設定エラー [{key}]: {str(e)}")
                            
            except Exception as e:
                print(f"パラメーター解析エラー: {str(e)}")
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

class MODSET_SetActiveButton(bpy.types.Operator):
    bl_idname = "modset.set_active_button"
    bl_label = "Set Active Button"
    bl_description = "Select this modifier"
    bl_options = {"REGISTER", "UNDO"}
    collection_index: bpy.props.IntProperty(name='collection index', default=0)

    def execute(self, context):
        bpy.context.scene.modset_active = self.collection_index
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

class MODSET_AddSelected(bpy.types.Operator):
    bl_idname = "modset.add_selected"
    bl_label = "Add Selected"
    bl_description = "Add selected Modifier to ModSet"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = bpy.context.scene
        if scene.modset_active < 0:
            scene.modset_active = -1
        item = scene.modset_preset.add()
        if (scene.modset_setting and
            utils.check_prop("bpy.context.scene.modset_preset", globals(), locals()) and
            len(scene.modset_preset) > scene.modset_active):
            scene.modset_preset.move(len(scene.modset_preset) - 1, scene.modset_active + 1)
            item = scene.modset_preset[scene.modset_active + 1]
        active_mod = bpy.context.object.modifiers.active
        if utils.check_prop("bpy.context.object.modifiers.active.node_group.id_data", globals(), locals()):
            if utils.check_prop("bpy.context.object.modifiers.active.node_group.library_weak_reference.filepath", globals(), locals()):
                filepath = active_mod.node_group.library_weak_reference.filepath
                if os.path.dirname(bpy.app.binary_path) in filepath:
                    orig = active_mod.name
                    dot = orig.find(".")
                    modname = orig[:dot] if dot != -1 else orig
                    item.modpath = os.path.join(filepath, 'NodeTree', modname).split('assets\\')[1]
                    item.modname = modname
                    item.modicon = 'GEOMETRY_NODES'
                    scene.modset_active += 1
                    bpy.ops.modset.autosave('INVOKE_DEFAULT')
                    params = utils.get_geometry_nodes_parameters(active_mod)
                    if params:
                        try:
                            item.parameters = json.dumps(params, separators=(',', ':'), ensure_ascii=False)
                            print(f"最終保存データ: {item.parameters}")
                            bpy.ops.modset.autosave('INVOKE_DEFAULT')
                        except Exception as e:
                            print(f"JSON変換エラー: {str(e)}")
                            item.parameters = ""
                    else:
                        print("警告: ジオメトリーノードのパラメーターが見つかりませんでした")
                        item.parameters = ""
                        bpy.ops.modset.autosave('INVOKE_DEFAULT')
                else:
                    orig = active_mod.name
                    dot = orig.find(".")
                    modname = orig[:dot] if dot != -1 else orig
                    for lib in bpy.context.preferences.filepaths.asset_libraries:
                        if lib.path in active_mod.node_group.library_weak_reference.filepath:
                            item.aseetlib = lib.name
                            item.modpath = os.path.join(os.path.basename(active_mod.node_group.library_weak_reference.filepath),
                                                        'NodeTree', modname)
                            item.modname = modname
                            item.modicon = 'GEOMETRY_NODES'
                            scene.modset_active += 1
                            bpy.ops.modset.autosave('INVOKE_DEFAULT')
                            params = utils.get_geometry_nodes_parameters(active_mod)
                            if params:
                                try:
                                    item.parameters = json.dumps(params, separators=(',', ':'), ensure_ascii=False)
                                    print(f"最終保存データ: {item.parameters}")
                                    bpy.ops.modset.autosave('INVOKE_DEFAULT')
                                except Exception as e:
                                    print(f"JSON変換エラー: {str(e)}")
                                    item.parameters = ""
                            else:
                                print("警告: ジオメトリーノードのパラメーターが見つかりませんでした")
                                item.parameters = ""
                                bpy.ops.modset.autosave('INVOKE_DEFAULT')
                            break
            else:
                for i, preset_item in enumerate(scene.modset_preset):
                    if preset_item == item:
                        scene.modset_preset.remove(i)
                        break
            # 保存対象のモディファイヤーから全パラメーターを取得
            if active_mod.type == 'NODES':
                params = utils.get_geometry_nodes_parameters(active_mod)
                if params:
                    item.parameters = json.dumps(params, separators=(',', ':'), ensure_ascii=False)
                    print(f"最終保存データ: {item.parameters}")
                    bpy.ops.modset.autosave('INVOKE_DEFAULT')
                else:
                    print("警告: ジオメトリーノードのパラメーターが見つかりませんでした")
                    item.parameters = ""
                    bpy.ops.modset.autosave('INVOKE_DEFAULT')
            else:
                params = utils.get_modifier_parameters(active_mod)
                item.parameters = json.dumps(params, separators=(',', ':'), ensure_ascii=False)
                print(f"Saved Parameters: {item.parameters}")
                bpy.ops.modset.autosave('INVOKE_DEFAULT')

        else:
            active_mod = bpy.context.view_layer.objects.active.modifiers.active
            item.modtype = active_mod.type
            item.modicon = utils.get_mod_icon(active_mod.type)
            orig = active_mod.name
            dot = orig.find(".")
            item.modname = orig[:dot] if dot != -1 else orig
            scene.modset_active += 1
            params = utils.get_modifier_parameters(active_mod)
            item.parameters = json.dumps(params, separators=(',', ':'), ensure_ascii=False)
            print(f"Saved Parameters: {item.parameters}")
            bpy.ops.modset.autosave('INVOKE_DEFAULT')
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

class MODSET_Autosave(bpy.types.Operator):
    bl_idname = "modset.autosave"
    bl_label = "AutoSave"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        utils.ui_data['values'] = []
        file_path = os.path.join(os.path.dirname(__file__), 'assets', 'prefs.json')
        with open(file_path, "w") as f:
            json.dump([], f)
        for i in range(len(bpy.context.scene.modset_preset)):
            if utils.check_prop(f"bpy.context.scene.modset_preset[{i}]", globals(), locals()):
                utils.add_to_ui_list(bpy.context.scene.modset_preset[i])
        utils.save_preset_json('Preset1')
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

class MODSET_LoadPreset(bpy.types.Operator):
    bl_idname = "modset.load_preset"
    bl_label = "Load Preset"
    bl_description = ("Load addon setting from Prefs Json file. "
                      "Put Json File in Prefs path first, then click this button.")
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = bpy.context.scene
        while len(scene.modset_prefs) < 3:
            scene.modset_prefs.add()
        scene.modset_preset.clear()
        file_json = os.path.join(os.path.dirname(__file__), 'assets', 'prefs.json')
        preset_to_load = 'Preset1'
        with open(file_json, 'r') as json_file:
            loaded = json.load(json_file)
        preset_data = None
        for item in loaded:
            if isinstance(item, dict) and preset_to_load in item:
                preset_data = item[preset_to_load]
                break
        if preset_data is None:
            print(f"Error: Preset '{preset_to_load}' not found.")
        else:
            p_data = preset_data.get("Preference", {})
            colnum = p_data.get("column_number", 2)
            show_name = p_data.get("show_mod_name", True)
            show_icon = p_data.get("show_mod_icon", True)
            show_add = p_data.get("show_add_always", True)
            show_preset = p_data.get("show_preset", False)
            for mod in preset_data.get("ModSet", []):
                item = scene.modset_preset.add()
                item.modname = mod.get("Name", "")
                item.modtype = mod.get("Type", "")
                item.modicon = mod.get("Icon", "")
                item.modpath = mod.get("Path", "")
                item.aseetlib = mod.get("AssetLibrary", "")
                parameters = mod.get("Parameters", {})
                item.parameters = parameters if isinstance(parameters, str) else json.dumps(parameters, ensure_ascii=False)
            prefs = scene.modset_prefs[0]
            prefs.columnnumber = colnum
            prefs.showmodicon = show_icon
            prefs.showmodname = show_name
            prefs.showaddalways = show_add
            prefs.sna_show_preset = show_preset
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

class MODSET_DeleteAll(bpy.types.Operator):
    bl_idname = "modset.delete_all"
    bl_label = "Delete All"
    bl_description = "Delete all ModSet"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        bpy.context.scene.modset_preset.clear()
        if bpy.context.screen:
            for area in bpy.context.screen.areas:
                area.tag_redraw()
        bpy.ops.modset.autosave('INVOKE_DEFAULT')
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

class MODSET_SelectIcon(bpy.types.Operator):
    bl_idname = "modset.select_icon"
    bl_label = "Select Icon"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}
    s_icon: bpy.props.StringProperty(name='Icon Name', default='')

    def execute(self, context):
        idx = bpy.context.scene.modset_active
        bpy.context.scene.modset_preset[idx].modicon = self.s_icon
        if bpy.context.screen:
            for area in bpy.context.screen.areas:
                area.tag_redraw()
        bpy.ops.modset.autosave('INVOKE_DEFAULT')
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

class MODSET_DeleteActive(bpy.types.Operator):
    bl_idname = "modset.delete_active"
    bl_label = "Delete Active"
    bl_description = "Delete active modifier from ModSet"
    bl_options = {"REGISTER", "UNDO"}
    collection_index: bpy.props.IntProperty(name='collection index', default=0)

    def execute(self, context):
        scene = bpy.context.scene
        if len(scene.modset_preset) > scene.modset_active:
            scene.modset_preset.remove(scene.modset_active)
        if len(scene.modset_preset) <= scene.modset_active:
            scene.modset_active = int(scene.modset_active - 1)
        bpy.ops.modset.autosave('INVOKE_DEFAULT')
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

class MODSET_OpenIconPicker(bpy.types.Operator):
    bl_idname = "modset.open_icon_picker"
    bl_label = "Open Icon Picker"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        bpy.ops.wm.call_panel(name="modset.icon_panel", keep_open=False)
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

class MODSET_MoveButton(bpy.types.Operator):
    bl_idname = "modset.move_button"
    bl_label = "Move Button"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}
    s_amount: bpy.props.IntProperty(name='amount', default=-2)

    def execute(self, context):
        scene = bpy.context.scene
        if self.s_amount < 0:
            scene.modset_preset.move(scene.modset_active, scene.modset_active + self.s_amount)
            scene.modset_preset.move(scene.modset_active + self.s_amount + 1, scene.modset_active)
        else:
            scene.modset_preset.move(scene.modset_active, scene.modset_active + self.s_amount)
            scene.modset_preset.move(scene.modset_active + self.s_amount - 1, scene.modset_active)
        scene.modset_active += self.s_amount
        bpy.ops.modset.autosave('INVOKE_DEFAULT')
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

# --- プロパティグループ ---
class MODSET_ModItem(bpy.types.PropertyGroup):
    modname: bpy.props.StringProperty(name='MODNAME', default='')
    modtype: bpy.props.StringProperty(name='MODTYPE', default='')
    modicon: bpy.props.StringProperty(name='MODICON', default='')
    modpath: bpy.props.StringProperty(name='MODPATH', default='', subtype='FILE_PATH')
    aseetlib: bpy.props.StringProperty(name='ASEETLIB', default='')
    # 新たに全パラメーターを保存するためのプロパティ
    parameters: bpy.props.StringProperty(name='Parameters', default='')

class MODSET_Prefs(bpy.types.PropertyGroup):
    presetname: bpy.props.StringProperty(name='PresetName', default='Preset')
    columnnumber: bpy.props.IntProperty(name='ColumnNumber', default=2, min=1, max=10, update=utils.update_colnum)
    showmodname: bpy.props.BoolProperty(name='ShowModName', default=True, update=utils.update_show_name)
    showmodicon: bpy.props.BoolProperty(name='ShowModIcon', default=False, update=utils.update_show_icon)
    showaddalways: bpy.props.BoolProperty(name='ShowAddAlways', default=True, update=utils.update_show_add)

classes = [
    MODSET_AddonPrefs,
    MODSET_OpenPrefsFolder,
    MODSET_ExpandPanel,
    MODSET_ToggleSetting,
    MODSET_UserButton,
    MODSET_SetActiveButton,
    MODSET_AddSelected,
    MODSET_Autosave,
    MODSET_LoadPreset,
    MODSET_DeleteAll,
    MODSET_SelectIcon,
    MODSET_DeleteActive,
    MODSET_OpenIconPicker,
    MODSET_MoveButton,
    MODSET_ModItem,
    MODSET_Prefs,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.modset_preset = bpy.props.CollectionProperty(type=MODSET_ModItem)
    bpy.types.Scene.modset_prefs = bpy.props.CollectionProperty(type=MODSET_Prefs)
    bpy.types.Scene.modset_isexpand = bpy.props.BoolProperty(name='IsExpand', default=False)
    bpy.types.Scene.modset_setting = bpy.props.BoolProperty(name='IsSetting', default=False)
    bpy.types.Scene.sna_show_preset = bpy.props.BoolProperty(name='SHOW_PRESET', default=False, update=utils.update_show_preset)
    bpy.types.Scene.modset_current = bpy.props.IntProperty(name='CURRENT_PRESET_ID', default=0, min=0, max=2)
    bpy.types.Scene.modset_active = bpy.props.IntProperty(name='ActiveButtonIndex', default=0)

def unregister():
    del bpy.types.Scene.modset_active
    del bpy.types.Scene.modset_current
    del bpy.types.Scene.sna_show_preset
    del bpy.types.Scene.modset_setting
    del bpy.types.Scene.modset_isexpand
    del bpy.types.Scene.modset_prefs
    del bpy.types.Scene.modset_preset
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
