from nicegui import ui
import savedata

def run_gui():
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
                ui.button('Load', on_click=lambda: savedata.parse_save(slot_radio.value))
            with ui.row():
                ui.label("Theme:")
                ui.button('Dark', on_click=dark.enable)
                ui.button('Light', on_click=dark.disable)

    

    ui.run()