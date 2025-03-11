import bpy
import os
import json
from . import utils

# --- Add-on Preferences ---
class MODSET_AddonPrefs(bpy.types.AddonPreferences):
    bl_idname = __package__

    def draw(self, context):
        layout = self.layout
        split = layout.split(factor=0.12843, align=False)
        split.label(text='Prefs file :', icon_value=0)
        split_path = split.split(factor=0.81193, align=False)
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
        
        # open folder based on OS
        if platform.system() == "Windows":
            subprocess.Popen(f'explorer "{folder_path}"')
        elif platform.system() == "Darwin":
            subprocess.Popen(['open', folder_path])
        else:
            subprocess.Popen(['xdg-open', folder_path])
            
        return {"FINISHED"}

# operator
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
        scene = bpy.context.scene
        preset = scene.modset_preset[self.collection_index]
        
        # Handle geometry node modifiers
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
        # Handle standard modifiers
        else:
            bpy.ops.object.modifier_add('INVOKE_DEFAULT', type=preset.modtype)
        
        new_mod = bpy.context.object.modifiers.active
        
        # ジオメトリノードパラメータ処理の簡略化
        if preset.parameters != "":
            try:
                params = json.loads(preset.parameters)
                
                # 標準モディファイヤーパラメータの復元
                if preset.modpath == '':
                    from .utils import restore_parameters
                    restore_parameters(new_mod, params)
                
                # ジオメトリノードパラメータ処理の簡略化
                else:  
                    for key, value in params.items():
                        # コレクション名参照の処理
                        if isinstance(value, str):
                            try:
                                # シーン内のコレクションを検索してみる
                                collection = bpy.data.collections.get(value)
                                if collection and key in new_mod:
                                    # コレクション参照をセット
                                    new_mod[key] = collection
                                    print(f"Restored collection reference for GN: {key} = {value}")
                                    continue
                                else:
                                    # コレクションが見つからない場合は通常の文字列として設定
                                    new_mod[key] = value
                            except Exception as e:
                                print(f"Failed to set collection value [{key}]: {str(e)}")
                                new_mod[key] = value
                        # オブジェクト参照などの複雑な値は無視し、基本的なデータ型のみを設定
                        elif isinstance(value, (int, float, bool)):
                            try:
                                new_mod[key] = value
                            except Exception as e:
                                print(f"Failed to set value [{key}]: {str(e)}")
                        # リスト型の値の処理
                        elif isinstance(value, list):
                            try:
                                new_mod[key] = value
                            except Exception as e:
                                print(f"Failed to set list value [{key}]: {str(e)}")
                
                # ジオメトリノードの場合、ビューポート更新を強制する
                if preset.modpath != '' or new_mod.type == 'NODES':
                    # モディファイヤーの表示状態を切り替えて強制的に更新させる
                    current_state = new_mod.show_viewport
                    new_mod.show_viewport = not current_state
                    new_mod.show_viewport = current_state
            except Exception as e:
                print(f"Parameter parsing error: {str(e)}")
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
                            print(f"Final saved data: {item.parameters}")
                            bpy.ops.modset.autosave('INVOKE_DEFAULT')
                        except Exception as e:
                            print(f"JSON serialization error: {str(e)}")
                            item.parameters = ""
                    else:
                        print("Warning: No parameters found in geometry nodes")
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
                                    print(f"Final saved data: {item.parameters}")
                                    bpy.ops.modset.autosave('INVOKE_DEFAULT')
                                except Exception as e:
                                    print(f"JSON serialization error: {str(e)}")
                                    item.parameters = ""
                            else:
                                print("Warning: No parameters found in geometry nodes")
                                item.parameters = ""
                                bpy.ops.modset.autosave('INVOKE_DEFAULT')
                            break
            else:
                for i, preset_item in enumerate(scene.modset_preset):
                    if preset_item == item:
                        scene.modset_preset.remove(i)
                        break
            # Retrieve all parameters from the target modifier
            if active_mod.type == 'NODES':
                params = utils.get_geometry_nodes_parameters(active_mod)
                if params:
                    item.parameters = json.dumps(params, separators=(',', ':'), ensure_ascii=False)
                    print(f"Final saved data: {item.parameters}")
                    bpy.ops.modset.autosave('INVOKE_DEFAULT')
                else:
                    print("Warning: No parameters found in geometry nodes")
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

class MODSET_ModItem(bpy.types.PropertyGroup):
    modname: bpy.props.StringProperty(name='MODNAME', default='')
    modtype: bpy.props.StringProperty(name='MODTYPE', default='')
    modicon: bpy.props.StringProperty(name='MODICON', default='')
    modpath: bpy.props.StringProperty(name='MODPATH', default='', subtype='FILE_PATH')
    aseetlib: bpy.props.StringProperty(name='ASEETLIB', default='')
    parameters: bpy.props.StringProperty(name='Parameters', default='')

class MODSET_Prefs(bpy.types.PropertyGroup):
    presetname: bpy.props.StringProperty(name='PresetName', default='Preset')
    columnnumber: bpy.props.IntProperty(name='ColumnNumber', default=2, min=1, max=10, update=utils.update_colnum)
    showmodname: bpy.props.BoolProperty(name='ShowModName', default=True, update=utils.update_show_name)
    showmodicon: bpy.props.BoolProperty(name='ShowModIcon', default=False, update=utils.update_show_icon)

class MODSET_DebugAddAllModifiers(bpy.types.Operator):
    """選択中のオブジェクトの全モディファイヤーをリストに追加"""
    bl_idname = "modset.debug_add_all_modifiers"
    bl_label = "Debug: Add All Modifiers"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    def execute(self, context):
        obj = context.active_object
        if not obj:
            self.report({'ERROR'}, "No active object")
            return {'CANCELLED'}

        for mod in obj.modifiers:
            # リストに新しいアイテムを追加
            item = context.scene.modset_preset.add()
            
            # GeometryNodesかどうかをチェック
            if mod.type == 'NODES' and mod.node_group:
                # ジオメトリノードの場合の処理
                item.modtype = mod.type
                item.modicon = 'GEOMETRY_NODES'
                item.modname = mod.name
                
                # アセットライブラリから追加されたノードグループの処理
                if hasattr(mod.node_group, 'library_weak_reference') and mod.node_group.library_weak_reference:
                    filepath = mod.node_group.library_weak_reference.filepath
                    
                    # Blender内蔵アセットの場合
                    if os.path.dirname(bpy.app.binary_path) in filepath:
                        modname = mod.name.split('.')[0] if '.' in mod.name else mod.name
                        item.modpath = os.path.join(filepath, 'NodeTree', modname).split('assets\\')[1]
                        item.aseetlib = ''
                    # カスタムアセットライブラリの場合
                    else:
                        modname = mod.name.split('.')[0] if '.' in mod.name else mod.name
                        for lib in context.preferences.filepaths.asset_libraries:
                            if lib.path in filepath:
                                item.aseetlib = lib.name
                                item.modpath = os.path.join(
                                    os.path.basename(filepath),
                                    'NodeTree', 
                                    modname
                                )
                                break
                
                # ジオメトリノードのパラメータを取得
                params = utils.get_geometry_nodes_parameters(mod)
            else:
                # 通常のモディファイヤーの場合
                item.modtype = mod.type
                item.modicon = utils.get_mod_icon(mod.type)
                item.modname = mod.name
                item.modpath = ''
                item.aseetlib = ''
                
                # 通常のモディファイヤーパラメータを取得
                params = utils.get_modifier_parameters(mod)
            
            # パラメータをシリアライズして保存
            try:
                item.parameters = json.dumps(params, separators=(',', ':'), ensure_ascii=False)
                print(f"保存したパラメータ({mod.name}): {params}")
            except Exception as e:
                print(f"パラメータシリアライズエラー({mod.name}): {str(e)}")
                item.parameters = "{}"
        
        bpy.ops.modset.autosave('INVOKE_DEFAULT')
        self.report({'INFO'}, f"Added {len(obj.modifiers)} modifiers")
        return {'FINISHED'}

class MODSET_DebugApplyAllModifiers(bpy.types.Operator):
    """登録済みモディファイヤーを全て適用"""
    bl_idname = "modset.debug_apply_all_modifiers"
    bl_label = "Debug: Apply All Modifiers"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    def execute(self, context):
        obj = context.active_object
        if not obj:
            self.report({'ERROR'}, "No active object")
            return {'CANCELLED'}

        # リストの順番通りにモディファイヤーを追加
        for item in context.scene.modset_preset:
            try:
                # ジオメトリノードの場合
                if item.modtype == 'NODES' or item.modpath:
                    if item.modpath:
                        # アセットライブラリからジオメトリノードを追加
                        lib_type = 'CUSTOM' if item.aseetlib else 'ESSENTIALS'
                        
                        # 既存のノードグループを削除して追加する方式
                        if hasattr(bpy.ops.object, 'modifier_add_node_group'):
                            bpy.ops.object.modifier_add_node_group(
                                'EXEC_DEFAULT',
                                asset_library_type=lib_type,
                                asset_library_identifier=item.aseetlib,
                                relative_asset_identifier=item.modpath
                            )
                        else:
                            # fallback: 別のモディファイヤー追加方法
                            print(f"ノードグループを直接追加できません: {item.modpath}")
                            continue
                    else:
                        # 標準ジオメトリノード
                        bpy.ops.object.modifier_add('EXEC_DEFAULT', type='NODES')
                else:
                    # 通常のモディファイヤー
                    bpy.ops.object.modifier_add('EXEC_DEFAULT', type=item.modtype)
                
                # 追加されたモディファイヤーを取得
                new_mod = obj.modifiers[-1]
                new_mod.name = item.modname
                
                # モディファイヤーのメインパネルけを開く
                new_mod.show_expanded = True
                
                # 元の表示設定を維持
                new_mod.show_viewport = False
                new_mod.show_render = False
                
                # パラメータを適用
                if item.parameters:
                    try:
                        params = json.loads(item.parameters)
                        
                        # ジオメトリノードの場合
                        if item.modtype == 'NODES' or item.modpath:
                            for key, value in params.items():
                                try:
                                    if key in new_mod:
                                        # コレクション名参照の処理
                                        if isinstance(value, str):
                                            # シーン内のコレクションを検索してみる
                                            collection = bpy.data.collections.get(value)
                                            if collection:
                                                # コレクション参照をセット
                                                new_mod[key] = collection
                                                print(f"Restored collection reference for GN: {key} = {value}")
                                                continue
                                        
                                        # オブジェクト参照の処理
                                        if isinstance(value, str) and value.startswith("OBJ:"):
                                            obj_name = value[4:]
                                            obj = bpy.data.objects.get(obj_name)
                                            if obj:
                                                try:
                                                    # ジオメトリノードの場合は直接代入ではなく、辞書形式でアクセス
                                                    new_mod[key] = obj
                                                    print(f"Restored object reference: {key} = {obj_name}")
                                                except Exception as e:
                                                    # 直接代入が失敗した場合の代替方法
                                                    try:
                                                        setattr(new_mod, key, obj)
                                                        print(f"Restored object reference (using setattr): {key} = {obj_name}")
                                                    except Exception as e2:
                                                        print(f"Failed to restore object reference [{key}]: {str(e2)}")
                                            else:
                                                print(f"Warning: Object {obj_name} not found")
                                        # リスト型の値の処理
                                        elif isinstance(value, list):
                                            if all(isinstance(x, (int, float)) for x in value):
                                                value = [float(x) for x in value]
                                            try:
                                                new_mod[key] = value
                                            except Exception as e:
                                                print(f"Failed to set list value [{key}]: {str(e)}")
                                        # その他の値の処理
                                        else:
                                            # 数値文字列の変換を試みる
                                            if isinstance(value, str):
                                                try:
                                                    if '.' in value:
                                                        value = float(value)
                                                    else:
                                                        value = int(value)
                                                except ValueError:
                                                    pass
                                            try:
                                                new_mod[key] = value
                                            except Exception as e:
                                                print(f"Failed to set value [{key}]: {str(e)}")
                                        print(f"Set geometry node parameter: {key} = {value} ({type(value)})")
                                except Exception as e:
                                    print(f"ジオメトリノード設定エラー [{key}]: {str(e)}")
                                    
                        else:
                            # 通常のモディファイヤー
                            utils.restore_parameters(new_mod, params)
                    except Exception as e:
                        print(f"パラメータ適用エラー: {str(e)}")
            except Exception as e:
                print(f"モディファイヤー追加エラー ({item.modname}): {str(e)}")
                continue

        self.report({'INFO'}, f"Applied {len(context.scene.modset_preset)} modifiers (All panels expanded)")
        return {'FINISHED'}

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
    MODSET_DebugAddAllModifiers,
    MODSET_DebugApplyAllModifiers,
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
