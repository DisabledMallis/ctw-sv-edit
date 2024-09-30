from binaryreader import BinaryReader
from datetime import datetime, timezone
from gamedata.WeaponType import WeaponType
import android
import os
import struct

remote_saves_dir = "/sdcard/Android/data/com.rockstargames.gtactw/files/"
data_dir = "data/"
backups_dir = data_dir + "backups/"
exports_dir = data_dir + "patched/"

SAVE_HEADER_OFFSET = 0
SAVE_HEADER_SIZE = 0x44
SAVE_CODE_OFFSET = SAVE_HEADER_OFFSET + SAVE_HEADER_SIZE
SAVE_CODE_SIZE = 0x194
SAVE_STATS_OFFSET = SAVE_CODE_OFFSET + SAVE_CODE_SIZE
SAVE_STATS_SIZE = 0x2A0
SAVE_SCRIPTS_OFFSET = SAVE_STATS_OFFSET + SAVE_STATS_SIZE
SAVE_SCRIPTS_SIZE = 0x938

def has_backups() -> bool:
    return os.path.exists(backups_dir)

def make_backup_folder():
    time = int(datetime.utcnow().timestamp())
    backup_dir = backups_dir + f"{time}" + "/"
    os.makedirs(backup_dir)
    return backup_dir

def backup_save():
    backup_dir = make_backup_folder()
    if not android.adb_started():
        print("ADB HAS NOT CONNECTED, CANNOT MAKE BACKUP!")
        return
    device = android.get_device()
    if not device:
        print("ADB STARTED, BUT DEVICE NOT CONNECTED. CANNOT MAKE  BACKUP!")
        return
    files = device.shell(f"ls {remote_saves_dir}").replace('\n', '').split("  ")
    for file in files:
        error = device.pull(f"{remote_saves_dir}{file}", f"{backup_dir}/{file}.dat")
        if error != None:
            print(f"Failed to backup {file}: {error}")

def upload_patches():
    if not android.adb_started():
        print("ADB HAS NOT CONNECTED, CANNOT MAKE BACKUP!")
        return
    device = android.get_device()
    if not device:
        print("ADB STARTED, BUT DEVICE NOT CONNECTED. CANNOT MAKE  BACKUP!")
        return
    files = device.shell(f"ls {remote_saves_dir}").replace('\n', '').split("  ")
    for file in files:
        patched_file = f"{exports_dir}/{file}.dat"
        if not os.path.exists(patched_file):
            continue
        error = device.push(f"{exports_dir}/{file}.dat", f"{remote_saves_dir}{file}")
        if error != None:
            print(f"Failed to upload patch {file}: {error}")

def most_recent_backup() -> str :
    most_recent: str = ""
    for backup in os.listdir(backups_dir):
        print(backup)
        most_recent = backup
    most_recent = backups_dir + most_recent + "/"
    return most_recent

def split_save(slot):
    backup = most_recent_backup()
    savefile = backup + f"savegame{slot}.dat"

    print(f"Splitting save '{savefile}'...")
    print(f"Save struct size {0xDB0}")
    print(f"\theader {0x44}")
    print(f"\tcode {0x194}")
    print(f"\tstats {0x2a0}")
    print(f"\tscript {0x938}")

    with open(savefile, 'rb') as sf:
        # Dump header
        with open(savefile + ".header", 'wb') as sw:
            for i in range(0, 0x44):
                sw.write(sf.read(1))
        # Dump code
        with open(savefile + ".code", 'wb') as sw:
            for i in range(0, 0x194):
                sw.write(sf.read(1))
        # Dump stats
        with open(savefile + ".stats", 'wb') as sw:
            for i in range(0, 0x2A0):
                sw.write(sf.read(1))
        # Dump script
        with open(savefile + ".script", 'wb') as sw:
            for i in range(0, 0x938):
                sw.write(sf.read(1))
class SaveData:
    mVersionStr: str = ""
    mSocialClubStamp: int = 0

    mMoney: int = 0
    mHealth: int = 0
    mArmor: int = 0

    mWeaponTypes: list(WeaponType) = []
    mWeaponAmmos: list = []

    def __init__(self):
        pass

    def load_header(self, sr: BinaryReader):
        sr.position = SAVE_HEADER_OFFSET + 8
        self.mVersionStr = sr.readStringC()
        print(f"mVersionStr: '{self.mVersionStr}'")
        sr.position = SAVE_HEADER_OFFSET + 0x40
        self.mSocialClubStamp = sr.readInt32()
        print(f"mSocialClubStamp: {self.mSocialClubStamp}")

    def load_code(self, sr: BinaryReader):
        sr.position = 0x4D
        self.mMoney = sr.readInt32()
        print(f"Money {self.mMoney}")
        sr.position = 0xF5
        self.mHealth = sr.readInt8()
        print(f"Health: {self.mHealth}")
        sr.position = 0xF6
        self.mArmor = sr.readInt8()
        print(f"Armor: {self.mArmor}")

        for i in range(0, 0xB):
            sr.position = 0xf7 + i
            typeValue = sr.readInt8()
            sr.position = 0x63 + i * 2
            ammoValue = sr.readInt16()
            typeName = str(typeValue)
            try:
                typeName = WeaponType(typeValue).name
            except:
                pass
            self.mWeaponTypes.append(typeValue)
            self.mWeaponAmmos.append(ammoValue)
            print(f"{i} - type: {typeName} ammo: {ammoValue}")

    def patch_code(self, pf):
        pf.seek(0x4D)
        pf.write(struct.pack('i', self.mMoney))
        pf.seek(0xF5)
        pf.write(struct.pack('b', self.mHealth))
        pf.seek(0xF6)
        pf.write(struct.pack('b', self.mArmor))

        for i in range(0, 0xB):
            pf.seek(0xf7 + i)
            pf.write(struct.pack('b', self.mWeaponTypes[i]))
            pf.seek(0x63 + i * 2)
            pf.write(struct.pack('h', self.mWeaponAmmos[i]))

        pf.flush()

def parse_save(slot: int) -> SaveData:
    backup = most_recent_backup()
    savefile = backup + f"savegame{slot}.dat"
    print(f"Loading {savefile}...")
    savedata: SaveData = SaveData()
    split_save(slot)
    print("Reading save file...")
    file_bytes: bytes = None
    with open(savefile, 'rb') as sf:
        file_bytes = sf.read()
    print(f"Read {len(file_bytes)} bytes")
    print("Parsing save data...")
    reader = BinaryReader(file_bytes, True)
    savedata.load_header(reader)
    savedata.load_code(reader)
    print("Loaded!")

    return savedata;

def save_patched(slot: int, modified: SaveData) -> str:
    backup = most_recent_backup()
    savefile = backup + f"savegame{slot}.dat"
    print(f"Patching {savefile}...")
    if not os.path.exists(exports_dir):
        os.makedirs(exports_dir)
    patchedfile = exports_dir + f"savegame{slot}.dat"
    print("Copying save file...")
    file_bytes: bytes = None
    with open(savefile, 'rb') as sf:
        file_bytes = sf.read()
    with open(patchedfile, 'wb') as pf:
        pf.write(file_bytes)
    print(f"Copied {len(file_bytes)} bytes of data")
    print("Applying patches...")
    with open(patchedfile, 'rb+') as pf:
        modified.patch_code(pf)
        print("Applied code patches!")
    print("Patched!")
    upload_patches()