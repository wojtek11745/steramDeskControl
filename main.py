import time
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
with open("game.txt", "r", encoding="utf-8") as plik:
    CATEGORIES["game"] = [line.strip() for line in plik if line.strip()]

last_scan = 0
last_scan2 = 0
esp_serials = {}
pot_values = [audio.master.get_volume(), 100, 0, 0]
ignore_system_update = False
volumeOld = 0
systenVolumeOld = 0
mediaVolumeOld = 0
gameVolumeOld = 0
while True:
    now = time.time()
    esp_manager.check_new_port()

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