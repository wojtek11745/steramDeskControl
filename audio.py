from pycaw.pycaw import AudioUtilities


class AudioController:
    def __init__(self):
        self.device = AudioUtilities.GetSpeakers()
        self._endpoint = self.device.EndpointVolume
        self._last_volume = self._endpoint.GetMasterVolumeLevelScalar()

    def set_volume(self, value: float):
        value = max(0.0, min(1.0, value))
        value = round(value, 2)

        if value != self._last_volume:
            if value != 0 :
                self._endpoint.SetMute(0, None) 
                
            self._endpoint.SetMasterVolumeLevelScalar(value, None)
            self._last_volume = value

        if value == 0:
            self._endpoint.SetMute(1, None)

    def get_volume(self) -> float:
        return self._endpoint.GetMasterVolumeLevelScalar()

    def get_volume_percent(self) -> int:
        return int(self.get_volume() * 100)

    def is_muted(self) -> bool:
        return bool(self._endpoint.GetMute())

    def device_change(self):
        Newdevice = AudioUtilities.GetSpeakers() 
        if Newdevice.id != self.device.id:
            self.device = Newdevice
            self._endpoint = self.device.EndpointVolume 
            self._last_volume = self._endpoint.GetMasterVolumeLevelScalar()
            return True

        return False
    

