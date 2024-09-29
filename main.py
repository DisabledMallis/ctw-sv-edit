from gui import run_gui
from threading import Thread
import savedata
import android

t = Thread(target=run_gui)
t.run()

android.start_adb()
device = android.get_device()

savedata.backup_save()