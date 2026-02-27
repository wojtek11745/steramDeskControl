from pycaw.pycaw import AudioUtilities


class MasterVolumeController:
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
    
class AppMixerController:
    def __init__(self):
        self.sessions = {}
        self.refresh_sessions()

    def refresh_sessions(self):
        new = {}

        for session in AudioUtilities.GetAllSessions():
            if session.Process:
                name = session.Process.name().lower()

                if name not in new:
                    new[name] = []

                new[name].append(session)

        self.sessions = new



    def set_app_volume(self, process_name: str, volume: float):
        volume = max(0.0, min(1.0, volume))
        process_name = process_name.lower()

        if process_name in self.sessions:
            valid_sessions = []
            for session in self.sessions[process_name]:
                try:
                    session.SimpleAudioVolume.SetMasterVolume(volume, None)
                    valid_sessions.append(session)
                except Exception:
                    pass
            self.sessions[process_name] = valid_sessions

    def set_category_volume(self, category_apps: list[str], volume: float):
        volume = max(0.0, min(1.0, volume))

        for app in category_apps:
            self.set_app_volume(app, volume)


class AudioController:
    def __init__(self):
        self.master = MasterVolumeController()
        self.mixer = AppMixerController()



