import time
import os
import threading
from esp import ESPManager  
from audio import AudioController
from utils import map_range

valid_ids = ["ESP32_784c28004f8c"]
esp_manager = ESPManager(valid_ids)
audio = AudioController()

script_dir = os.path.dirname(os.path.abspath(__file__))

user_command = ""
def read_input():
    global user_command
    while True:
        text = input()
        if text.strip():
            user_command = text.strip()

threading.Thread(target=read_input, daemon=True).start()

last_scan = 0
last_scan2 = 0
esp_serials = {}
pot_values = [audio.master.get_volume(), 100, 0, 0]
ignore_system_update = False
volumeOld = 0
systemVolumeOld = 0

adding_state = None
not_known_apps = []
selected_app = None
category_name = None

def get_category(location, folder_name):
    file_folder_path = os.path.join(location, folder_name)

    if not os.path.exists(file_folder_path):
        os.makedirs(file_folder_path)

    categories = {}

    category_files = os.listdir(file_folder_path)

    for filename in category_files:
        if filename.endswith(".txt"):
            name = filename.removesuffix(".txt")    
            file_path = os.path.join(file_folder_path, filename)

            with open(file_path, "r", encoding="utf-8") as f:
                categories[name] = [line.strip() for line in f if line.strip()]
    return categories
CATEGORIES = get_category(script_dir, "categories")

def check_category_name(CATEGORIES, text):
    category_name = text[4:]

    if category_name in CATEGORIES:
        return category_name
        
    print("invalid category name")
    return None

def retrieval_unknown_apps(running_apps, cat):
    known_apps = {exe.lower() for exe in sum(cat.values(), [])}
    not_known_apps =  list(running_apps - known_apps)

    if not not_known_apps:
        print("lack applications to add")
        return [], None

    for index, app in enumerate(not_known_apps, start=1):
        print(f"[{index}] {app}")
    print("choose app to add")
    return not_known_apps, "selection_app_to_add"

def choose_from(number, items):
    if 0 <= number < len(items):
        return items[number]
    
    print(f"invalid number. choose number between 1 to {len(items)}")
    return None

def add_to_file_list_txt(file_name, location, item):
    file_path = os.path.join(location, (f"{file_name}.txt"))
    needs_newline = False

    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

            if content and not content.endswith("\n"):
                needs_newline = True

    with open(file_path, "a", encoding="utf-8") as file:
        if needs_newline:
            file.write("\n")

        file.write(f"{item}\n")
        print(f"{item} been added to {file_name}.txt")
    

while True:
    now = time.time()
    esp_manager.check_new_port()

    if user_command:
        reset = False
        text = user_command
        user_command = ""
        
        if text.startswith("add.") and adding_state is None:
            category_name = check_category_name(CATEGORIES, text)
            
            if category_name:
                running_apps = audio.get_apps()
                not_known_apps, adding_state = retrieval_unknown_apps(running_apps, CATEGORIES)
                if not not_known_apps:
                    reset = True
            else:
                reset = True

        elif adding_state == "selection_app_to_add" and text.isdigit():
            selected_app = choose_from((int(text) - 1), not_known_apps)

            if selected_app is not None:
                path = os.path.join(script_dir, "categories")
                add_to_file_list_txt(category_name ,path ,selected_app)
                CATEGORIES[category_name].append(selected_app)
                reset = True

        else:
            print("invalid command")
            reset = True

        if reset:
            adding_state = None
            not_known_apps = []
            selected_app = None
            category_name = None

    if now - last_scan > 0.5:
        esp_manager.remove_disconnected_ports()
        audio.mixer.refresh_sessions()
        last_scan = now

    events  = esp_manager.read_data()
    for event in events:
        if event.get("type") == "device_confirmed":
            print("Nowe urządzenie potwierdzone!")

            current_volume = audio.master.get_volume()
            esp_manager.send_volume(current_volume)
        elif "data" in event:
            data = event["data"]
            if data["t"] == "p":  # potencjometr
                pot_id = data["i"]
                value = data["v"]
                pot_values[pot_id] = value
                print(f"Pot {pot_id} -> {value}")


    systemVolume = audio.master.get_volume()

    if now - last_scan2 > 0.3:
        if(audio.master.device_change()):
            esp_manager.send_volume(systemVolume)
        last_scan2 = now

    volume_value = round(map_range(pot_values[0], 0, 1023, 0.0, 1.0), 2)

    if volume_value != volumeOld:
        audio.master.set_volume(volume_value)
        volumeOld = volume_value
        ignore_system_update = True
        print(f"- Muted: {bool(audio.master.is_muted())}")
        print(f"- Volume: {audio.master.get_volume_percent()}%")

    if abs(systemVolumeOld - systemVolume) >= 0.01:
        if not ignore_system_update:
            esp_manager.send_volume(systemVolume)
        else:
            ignore_system_update = False

    systemVolumeOld = systemVolume


    mediaVolume = round(map_range(pot_values[1], 0, 1023, 0.0, 1.0), 2)
    audio.mixer.set_category_volume("media", CATEGORIES["media"], mediaVolume)

    gameVolume = round(map_range(pot_values[2], 0, 1023, 0.0, 1.0), 2)
    audio.mixer.set_category_volume("game", CATEGORIES["game"], gameVolume)

    time.sleep(0.01)


