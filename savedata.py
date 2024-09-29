from binaryreader import BinaryReader
from datetime import datetime, timezone
import android
import os

remote_saves_dir = "/sdcard/Android/data/com.rockstargames.gtactw/files/"
data_dir = "data/"
backups_dir = data_dir + "backups/"

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
        error = device.pull(f"/sdcard/Android/data/com.rockstargames.gtactw/files/{file}", f"{backup_dir}/{file}.dat")
        if error != None:
            print(f"Failed to backup {file}: {error}")

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
    mVersionStr: str
    mSocialClubStamp: int = 0

    mMoney: int = 0
    mArmor: int = 0

    def __init__(self):
        pass

    def load_header(self, sr: BinaryReader):
        sr.position = SAVE_HEADER_OFFSET + 8
        mVersionStr = sr.readStringC()
        print(f"mVersionStr: '{mVersionStr}'")
        sr.position = SAVE_HEADER_OFFSET + 0x40
        mSocialClubStamp = sr.readInt32()
        print(f"mSocialClubStamp: {mSocialClubStamp}")

    def load_code(self, sr: BinaryReader):
        sr.position = 0x4C
        mMoney = sr.readInt32()
        print(f"Money {mMoney}")
        sr.position = 0xF5
        mArmor = sr.readInt8()
        print(f"Armor: {mArmor}")

        sr.position = 0xf6
        for i in range(0, 0xB):
            print(f"{i} - {sr.readInt16()}")


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