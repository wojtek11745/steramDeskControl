import serial.tools.list_ports
import serial
import json
from utils import map_range



class ESPManager:
    def __init__(self, valid_ids):
        self.valid_ids = valid_ids
        self.esp_serials = {}


    def find_all_esp32(self):
        ports = serial.tools.list_ports.comports()
        esp_ports = []
        for port in ports:
            # VID/PID dla ESP32 (CH340 lub CP210x)
            if port.vid in [0x10C4, 0x1A86]:
                esp_ports.append(port.device)
        return esp_ports


    def open_port(self, port):
        try:
            ser = serial.Serial(port, 115200, timeout=1)
            self.esp_serials[port] = {
                "serial": ser,
                "id": None,
                "confirmed": False
            }
        except serial.SerialException as e:
            print(f"Nie udało się otworzyć portu {port}: {e}")


    def check_new_port(self):
        any_confirmed = any(info["confirmed"] for info in self.esp_serials.values())
        
        if not any_confirmed:
            for port in self.find_all_esp32():
                self.open_port(port)
    

    def remove_disconnected_ports(self):
        available_ports = [p.device for p in serial.tools.list_ports.comports()]
        for port in list(self.esp_serials.keys()):
            if port not in available_ports:
                print(f"ESP32 na porcie {port} odłączone!")
                self.esp_serials[port]["confirmed"] = False
                self.esp_serials[port]["id"] = None
                try:
                    self.esp_serials[port]["serial"].close() 
                except:
                    pass
                self.esp_serials.pop(port, None)


    def read_data(self):
        events = []
        for port, info in list(self.esp_serials.items()):
            ser = info["serial"]
            try:
                if ser.in_waiting:
                    line = ser.readline().decode("utf-8", errors="ignore").strip()
                    if line.startswith("DEVICE_ID:") and not info["confirmed"]:
                        event = self._handle_device_id(port, info, line)
                        if event:
                            events.append(event)

                    elif line.startswith("DATA:") and info["confirmed"]:
                        data = json.loads(line.replace("DATA:", ""))
                        events.append({"port": port, "data": data})
                        
            except serial.SerialException as e:
                print(f"Błąd portu {port}: {e}, usuwam port z listy")
                try:
                    ser.close()
                except:
                    pass
                self.esp_serials.pop(port, None)
                
        return events
    
    
    def _handle_device_id(self, port, info, line):
        device_id = line.split("DEVICE_ID:")[1]
        
        if device_id in self.valid_ids:
            info["id"] = device_id
            info["confirmed"] = True
            try:
                info["serial"].write(f"ACK:{device_id}\n".encode("utf-8"))
            except serial.SerialException:
                pass
            print(f"Potwierdzono ESP32 {device_id} na porcie {port}")
            return {
                "type": "device_confirmed",
                "port": port
            }
        else:
            print(f"Nieznane ID: {device_id} na porcie {port}")
            return None


    def send_volume(self, volume):
        x = round(map_range(volume, 0, 1.0, 0.0, 1023))
        volume = max(0.0, min(1.0, volume))
        message = f"FADER;0;SET;{x}\n"
        for port, info in self.esp_serials.items():
            if info["confirmed"]:
                try:
                    info["serial"].write(message.encode("utf-8"))
                except serial.SerialException:
                    pass
