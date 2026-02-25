import time
from esp import ESPManager  
from audio import AudioController
from utils import map_range

valid_ids = ["ESP32_784c28004f8c"]
esp_manager = ESPManager(valid_ids)
audio = AudioController()

last_scan = 0
last_scan2 = 0
esp_serials = {}
pot_values = [audio.get_volume(), 0, 0, 0]
ignore_system_update = False
volumeOld = 0
masterVolumeOld = 0
while True:
    now = time.time()
    esp_manager.check_new_port()

    if now - last_scan > 1:
        esp_manager.remove_disconnected_ports()
        last_scan = now

    events  = esp_manager.read_data()
    for event in events:
        if event.get("type") == "device_confirmed":
            print("Nowe urządzenie potwierdzone!")

            current_volume = audio.get_volume()
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
    masterVolume = audio.get_volume()
    
    if now - last_scan2 > 0.3:
        if(audio.device_change()):
            esp_manager.send_volume(masterVolume)
        last_scan2 = now

    volume_value = round(map_range(pot_values[0], 0, 1023, 0.0, 1.0), 2)

    if volume_value != volumeOld:
        audio.set_volume(volume_value)
        volumeOld = volume_value
        ignore_system_update = True
        print(f"- Muted: {bool(audio.is_muted())}")
        print(f"- Volume: {audio.get_volume_percent()}%")

    

    if abs(masterVolumeOld - masterVolume) >= 0.01:
        if not ignore_system_update:
            esp_manager.send_volume(masterVolume)
        else:
            ignore_system_update = False

    masterVolumeOld = masterVolume
    time.sleep(0.01)