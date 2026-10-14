import time
import os
import threading
import category_manager
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
CATEGORIES = category_manager.get_category(script_dir, "categories")

while True:
    now = time.time()
    esp_manager.check_new_port()

    if user_command:
        reset = False
        text = user_command
        user_command = ""
        
        if text.startswith("add.") and adding_state is None:
            category_name = category_manager.check_category_name(CATEGORIES, text)
            
            if category_name:
                running_apps = audio.get_apps()
                not_known_apps, adding_state = category_manager.retrieval_unknown_apps(running_apps, CATEGORIES)
                if not not_known_apps:
                    reset = True
            else:
                reset = True

        elif adding_state == "selection_app_to_add" and text.isdigit():
            selected_app = category_manager.choose_from((int(text) - 1), not_known_apps)

            if selected_app is not None:
                path = os.path.join(script_dir, "categories")
                category_manager.add_to_file_list_txt(category_name ,path ,selected_app)
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


