from ppadb.client import Client as AdbClient

client: AdbClient = None

def start_adb():
    global client
    print("Connecting to ADB...")
    client = AdbClient(host="127.0.0.1", port=5037)
    print(f"Connected ADB version: {client.version()}")

def adb_started() -> bool:
    return client != None

def get_device():
    return client.devices()[0]

