from pycaw.pycaw import AudioUtilities
import serial
import serial.tools.list_ports
import time
import json

last_scan = 0
device = AudioUtilities.GetSpeakers()
endpoint = device.EndpointVolume

volumeOld = endpoint.GetMasterVolumeLevelScalar()
volume_value = volumeOld
masterVolume = endpoint.GetMasterVolumeLevelScalar()
masterVolumeOld = masterVolume

def find_all_esp32():
    ports = serial.tools.list_ports.comports()
    esp_ports = []
    for port in ports:
        # VID/PID dla ESP32 (CH340 lub CP210x)
        if port.vid in [0x10C4, 0x1A86]:
            esp_ports.append(port.device)
    return esp_ports

def map_range(x, in_min, in_max, out_min, out_max):
    x = max(min(x, in_max), in_min)  # clamp
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

valid_ids = ["ESP32_784c28004f8c"]
esp_serials = {}
for port in find_all_esp32():
    try:
        ser = serial.Serial(port, 115200, timeout=1)
        esp_serials[port] = {
            "serial": ser,
            "id": None,
            "confirmed": False
        }
    except serial.SerialException as e:
        print(f"Nie udało się otworzyć portu {port}: {e}")

pot_values = [184, 0, 0, 0]

while True:
    now = time.time()

        # Sprawdzenie nowych portów
    any_confirmed = any(info["confirmed"] for info in esp_serials.values())
    if now - last_scan > 1:
        available_ports = [p.device for p in serial.tools.list_ports.comports()]
        if not any_confirmed:
            for port in find_all_esp32():  # tylko ESP32
                if port not in esp_serials:
                    try:
                        ser = serial.Serial(port, 115200, timeout=1)
                        esp_serials[port] = {"serial": ser, "id": None, "confirmed": False}
                        print(f"Nowy port ESP32 wykryty: {port}")
                    except serial.SerialException as e:
                        print(f"Nie udało się otworzyć portu {port}: {e}")
        last_scan = now

    available_ports = [p.device for p in serial.tools.list_ports.comports()]
    for port in list(esp_serials.keys()):
        if port not in available_ports:
            print(f"ESP32 na porcie {port} odłączone!")
            esp_serials[port]["confirmed"] = False
            esp_serials[port]["id"] = None
            try:
                esp_serials[port]["serial"].close() 
            except:
                pass
            esp_serials.pop(port, None)



    for port, info in list(esp_serials.items()):
        ser = info["serial"]
        try:
            # odczyt tylko jeśli port wciąż działa
            if ser.in_waiting:
                line = ser.readline().decode("utf-8", errors="ignore").strip()

                if line.startswith("DEVICE_ID:") and not info["confirmed"]:
                    device_id = line.split("DEVICE_ID:")[1]
                    if device_id in valid_ids:
                        info["id"] = device_id
                        info["confirmed"] = True
                        try:
                            ser.write(f"ACK:{device_id}\n".encode("utf-8"))
                        except serial.SerialException:
                            pass
                        print(f"Potwierdzono ESP32 {device_id} na porcie {port}")
                    else:
                        print(f"Nieznane ID: {device_id} na porcie {port}")

                elif line.startswith("DATA:") and info["confirmed"]:
                    data = json.loads(line.replace("DATA:", ""))
                    if data["t"] == "p":
                        pot_id = data["i"]
                        value = data["v"]
                        pot_values[pot_id] = value 
                        print("Pot", pot_id, "->", value)
        except serial.SerialException as e:
            print(f"Błąd portu {port}: {e}, usuwam port z listy")
            try:
                ser.close()
            except:
                pass
            esp_serials.pop(port, None)

            
    volume_value = round(map_range(pot_values[0], 0, 1023, 0.0, 1.0), 2)
    if volume_value != volumeOld:
        volumeOld = volume_value
        endpoint.SetMasterVolumeLevelScalar(volume_value, None)
        ignore_system_update = True
        volume_percent = int(endpoint.GetMasterVolumeLevelScalar() * 100)
        print(f"Audio output: {device.FriendlyName}")
        print(f"- Muted: {bool(endpoint.GetMute())}")
        print(f"- Volume level: {volume_percent}%")
        print(endpoint.GetMasterVolumeLevelScalar())

    
    masterVolume = endpoint.GetMasterVolumeLevelScalar()
    if abs(masterVolumeOld - masterVolume) >= 0.01:
        if not ignore_system_update:
            x = round(map_range(masterVolume, 0, 1.0, 0.0, 1023))
            message = f"FADER;0;SET;{x}\n"

            for port, info in esp_serials.items():
                if info["confirmed"]:
                    try:
                        info["serial"].write(message.encode("utf-8"))
                    except serial.SerialException:
                        pass
        else:
            ignore_system_update = False

    masterVolumeOld = masterVolume