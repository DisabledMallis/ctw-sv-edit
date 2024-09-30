from nicegui import ui, binding
from gamedata.WeaponType import WeaponType
import savedata

active_save: savedata.SaveData = savedata.SaveData()

class SlotProperties:
    weapon_type = binding.BindableProperty()
    weapon_ammos = binding.BindableProperty()

class SaveProperties:
    money = binding.BindableProperty()
    health = binding.BindableProperty()
    armor = binding.BindableProperty()

    weapons = []

    def __init__(self):
        for i in range(0, 11):
            self.weapons.append(SlotProperties())

    def load(self, save: savedata.SaveData):
        self.money = save.mMoney
        self.health = (float(save.mHealth) / 127.0) * 100.0
        self.armor = (float(save.mArmor) / 127.0) * 100.0
        for i in range(0, 11):
            self.weapons[i].weapon_type = save.mWeaponTypes[i]
            self.weapons[i].weapon_ammos = save.mWeaponAmmos[i]

    def save(self):
        global active_save
        active_save.mMoney = self.money
        active_save.mHealth = int((self.health / 100.0) * 127)
        active_save.mArmor = int((self.armor / 100.0) * 127)
        for i in range(0, 11):
            active_save.mWeaponTypes[i] = int(self.weapons[i].weapon_type)
            active_save.mWeaponAmmos[i] = int(self.weapons[i].weapon_ammos)

save_props = SaveProperties()

def load_save(slot: int):
    global active_save
    active_save = savedata.parse_save(slot)
    save_props.load(active_save)

def patch_save(slot: int):
    global active_save
    save_props.save()
    savedata.save_patched(slot, active_save)

def run_gui():
    global active_save
    global money_input
    dark = ui.dark_mode()
    with ui.tabs().classes('w-full') as tabs:
        info = ui.tab('Info')
        player = ui.tab('Player')

    with ui.tab_panels(tabs, value=info).classes('w-full'):
        with ui.tab_panel(info):
            ui.label("GTA:CTW save editor").classes('text-xl')
            with ui.row():
                ui.label("Save file:")
                slot_radio = ui.radio([0,1], value=1).props('inline')
                ui.button('Load', on_click=lambda: load_save(slot_radio.value))
                ui.button('Patch', on_click=lambda: patch_save(slot_radio.value))
            with ui.row():
                ui.label("Theme:")
                ui.button('Dark', on_click=dark.enable)
                ui.button('Light', on_click=dark.disable)

        with ui.tab_panel(player):
            ui.label("Player Stats").classes('text-lg')
            ui.number(label="Money").bind_value(save_props, 'money')
            ui.separator()
            with ui.row().classes('w-full'):
                ui.label("Health")
                health_slider = ui.slider(min=0, max=100, step=1).bind_value(save_props, 'health')
                ui.label().bind_text_from(health_slider, 'value')
            ui.separator()
            with ui.row().classes('w-full'):
                ui.label("Armor")
                armor_slider = ui.slider(min=0, max=100, step=1).bind_value(save_props, 'armor')
                ui.label().bind_text_from(armor_slider, 'value')

            ui.label("Player Inventory").classes('text-lg')
            for i in range(0, 11):
                with ui.row():
                    ui.label(f"Slot {i}")
                    weapon_select = ui.select({j.value: j.name for j in WeaponType}).bind_value(save_props.weapons[i], 'weapon_type')
                    ui.number(label="Ammo").bind_value(save_props.weapons[i], 'weapon_ammos')

    ui.run()