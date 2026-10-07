import time
import os
import threading
from esp import ESPManager  
from audio import AudioController
from utils import map_range

valid_ids = ["ESP32_784c28004f8c"]
esp_manager = ESPManager(valid_ids)
audio = AudioController()
CATEGORIES = {
    "media": ["discord.exe", "firefox.exe",],
    "game": [],
}
script_dir = os.path.dirname(os.path.abspath(__file__))
game_file_path = os.path.join(script_dir, "game.txt")

with open(game_file_path, "r", encoding="utf-8") as plik:
    CATEGORIES["game"] = [line.strip() for line in plik if line.strip()]

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
systenVolumeOld = 0
mediaVolumeOld = 0
gameVolumeOld = 0

adding_state = None
not_known_apps = []
selected_app = None

while True:
    now = time.time()
    esp_manager.check_new_port()

    if user_command:

        reset = False
        text = user_command
        user_command = ""
        if text == "add.game" and adding_state is None:
            running_apps = audio.get_apps();
            known_apps = {exe.lower() for exe in sum(CATEGORIES.values(), [])}
            not_known_apps =  list(running_apps - known_apps)

            if not not_known_apps:
                print("lack applications to add")
            else:
                for index, app in enumerate(not_known_apps, start=1):
                    print(f"[{index}] {app}")
                print("choose app to add")
                adding_state = "selection_app_to_add"
        elif adding_state == "selection_app_to_add":
            if text.isdigit():
                num = int(text) - 1
                if 0 <= num < len(not_known_apps):
                    selected_app = not_known_apps[num]
                    print(f"you choose {selected_app} add it to game section Y/N")
                    adding_state = "confirmation"
                else:
                    print(f"invalid number. choose number between 1 to {len(not_known_apps)}")
            else:
                print("invalid commadn")
                reset = True

        elif(adding_state == "confirmation"):
            if text.lower() in ["yes", "y"]:
                CATEGORIES["game"].append(selected_app)
                with open(game_file_path, "a", encoding="utf-8") as file:
                    file.write(f"\n{selected_app}")
                    print(f"{selected_app} been added to game")
            elif text.lower() in ["no", "n"]:
                print("return to main menu")
                reset = True

        else:
            print("invalid commadn")
            reset = True

        if reset:
            adding_state = None
            not_known_apps = []
            selected_app = None


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
    # odczyt danych z ESP32


    # ustawienie głośności
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

    

    if abs(systenVolumeOld - systemVolume) >= 0.01:
        if not ignore_system_update:
            esp_manager.send_volume(systemVolume)
        else:
            ignore_system_update = False

    systenVolumeOld = systemVolume


    mediaVolume = round(map_range(pot_values[1], 0, 1023, 0.0, 1.0), 2)
    if abs(mediaVolumeOld - mediaVolume) >= 0.01:
        audio.mixer.set_category_volume(CATEGORIES["media"], mediaVolume)
    mediaVolumeOld = mediaVolume

    gameVolume = round(map_range(pot_values[2], 0, 1023, 0.0, 1.0), 2)
    if abs(gameVolumeOld - gameVolume) >= 0.01:
        audio.mixer.set_category_volume(CATEGORIES["game"], gameVolume)
    gameVolumeOld = gameVolume

    time.sleep(0.01)