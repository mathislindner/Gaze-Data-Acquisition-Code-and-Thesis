import uvc
import numpy as np

import time

from uvc_utils import Exposure_Time, Check_Frame_Stripes, InitialisationError


DEV_SETTINGS = {

    'pupil_invisible': {
        'eye_left': {
            'name': 'PI left v1', 
            'uid': '1:126', 
            'label': 'left_pi',
            'frame_size': (400, 400), # 192, 192 fps:200
            'fps': 120, 
            },
        'eye_right': {
            'name': 'PI right v1', 
            'uid': '1:127', 
            'label': 'right_pi',
            'frame_size': (400, 400), # 192, 192 fps:200
            'fps': 120, 
            },
        'world': {
            'name': 'PI world v1', 
            'uid': '1:4', 
            'label': 'world_pi',
            'frame_size': (1088, 1080), 
            'fps': 30,  
            },
    },

    'aegis_core': {
        'eye_left': {
            'name': 'Pupil Cam2 ID1', 
            'uid': '1:7', 
            'label': 'left_ac',
            'frame_size': (400, 400), # 192, 192 fps:200
            'fps': 120, 
            },
        'eye_right': {
            'name': 'Pupil Cam2 ID0', 
            'uid': '1:9', 
            'label': 'right_ac',
            'frame_size': (400, 400), # 192, 192 fps:200
            'fps': 120, 
            },
        'world': {
            'name': 'USB 2.0 Camera', 
            'uid': '1:8', 
            'label': 'world_ac',
            'frame_size': (1280, 960), # can also do (1600, 1200) (1920, 1080)
            'fps': 25, 
            },
    }
}

# UVC_Source class taken and modified from:
# https://github.com/pupil-labs/pupil/blob/master/pupil_src/shared_modules/video_capture/uvc_backend.py
class UVC_Source:
    """
    Camera Capture is a class that encapsualtes uvc.Capture:
    """

    def __init__(
        self,
        frame_size,
        frame_rate,
        label,
        name=None,
        preferred_names=(),
        uid=None,
        uvc_controls={},
        check_stripes=True,
        exposure_mode="manual",
    ):

        self.label = label

        self.should_check_stripes = False
        self.uvc_capture = None
        self._last_ts = None
        self._restart_in = 3
        assert name or preferred_names or uid

        self.devices = uvc.Device_List()

        devices_by_name = {dev["name"]: dev for dev in self.devices}

        # if uid is supplied we init with that
        if uid:
            try:
                self.uvc_capture = uvc.Capture(uid)
            except uvc.OpenError:
                self.print(
                    f"Camera matching uid:{uid} found but not available"
                )
            except uvc.InitError:
                self.print("Camera failed to initialize.")
            except uvc.DeviceNotFoundError:
                self.print(f"No camera found that matched uid:{uid}")

        # otherwise we use name or preffered_names
        else:
            if name:
                preferred_names = (name,)
            else:
                pass
            assert preferred_names

            # try to init by name
            for name in preferred_names:
                for d_name in devices_by_name.keys():
                    if name in d_name:
                        uid_for_name = devices_by_name[d_name]["uid"]
                        try:
                            self.uvc_capture = uvc.Capture(uid_for_name)
                            break
                        except uvc.OpenError:
                            self.print(
                                f"{uid_for_name} matches {name} but is already in use "
                                "or blocked."
                            )
                        except uvc.InitError:
                            self.print("Camera failed to initialize.")
                if self.uvc_capture:
                    break

        # checkframestripes will be initialized accordingly in configure_capture()
        self.enable_stripe_checks = check_stripes
        self.exposure_mode = exposure_mode
        self.stripe_detector = None
        self.preferred_exposure_time = None

        # check if we were sucessfull
        if not self.uvc_capture:
            self.print("Could not connect to device! No images will be supplied.")
            #raise ConnectionError
            self.name_backup = preferred_names
            self.frame_size_backup = frame_size
            self.frame_rate_backup = frame_rate
            self.exposure_time_backup = None
            # self._intrinsics = Camera_Model.from_file(
            #     self.g_pool.user_dir, self.name, self.frame_size
            # )
        else:
            self.configure_capture(frame_size, frame_rate, uvc_controls)
            self.name_backup = (self.name,)
            self.frame_size_backup = frame_size
            self.frame_rate_backup = frame_rate
            controls_dict = dict(
                [(c.display_name, c) for c in self.uvc_capture.controls]
            )
            try:
                self.exposure_time_backup = controls_dict[
                    "Absolute Exposure Time"
                ].value
            except KeyError:
                self.exposure_time_backup = None

        self.backup_uvc_controls = {}
        
    
    def configure_capture(self, frame_size, frame_rate, uvc_controls):
        # Set camera defaults. Override with previous settings afterwards
        if "Pupil Cam" in self.uvc_capture.name:
            # if platform.system() == "Windows":
            #     # NOTE: Hardware timestamps seem to be broken on windows. Needs further
            #     # investigation! Disabling for now.
            #     # TODO: Find accurate offsets for different resolutions!
            #     offsets = {"ID0": -0.015, "ID1": -0.015, "ID2": -0.07}
            #     match = re.match(r"Pupil Cam\d (?P<cam_id>ID[0-2])", self.name)
            #     if not match:
            #         logger.debug(f"Could not parse camera name: {self.name}")
            #         self.ts_offset = -0.01
            #     else:
            #         self.ts_offset = offsets[match.group("cam_id")]

            # else:
            #     # use hardware timestamps
            #     self.ts_offset = None
            self.ts_offset = None
        else:
            self.print(
                f"Hardware timestamps not supported for {self.uvc_capture.name}. "
                "Using software timestamps."
            )
            self.ts_offset = -0.1

        # UVC setting quirks:
        controls_dict = dict([(c.display_name, c) for c in self.uvc_capture.controls])

        if (
            ("Pupil Cam2" in self.uvc_capture.name)
            or ("Pupil Cam3" in self.uvc_capture.name)
        ) and frame_size == (320, 240):
            frame_size = (192, 192)

        self.frame_size = frame_size
        self.frame_rate = frame_rate

        try:
            controls_dict["Auto Focus"].value = 0
        except KeyError:
            pass

        if "Pupil Cam1" in self.uvc_capture.name:

            if "ID0" in self.uvc_capture.name or "ID1" in self.uvc_capture.name:

                self.uvc_capture.bandwidth_factor = 1.3

                try:
                    controls_dict["Auto Exposure Priority"].value = 0
                except KeyError:
                    pass

                try:
                    controls_dict["Auto Exposure Mode"].value = 1
                except KeyError:
                    pass

                try:
                    controls_dict["Saturation"].value = 0
                except KeyError:
                    pass

                try:
                    controls_dict["Absolute Exposure Time"].value = 63
                except KeyError:
                    pass

                try:
                    controls_dict["Backlight Compensation"].value = 2
                except KeyError:
                    pass

                try:
                    controls_dict["Gamma"].value = 100
                except KeyError:
                    pass

            else:
                self.uvc_capture.bandwidth_factor = 2.0
                try:
                    controls_dict["Auto Exposure Priority"].value = 1
                except KeyError:
                    pass

        elif (
            "Pupil Cam2" in self.uvc_capture.name
            or "Pupil Cam3" in self.uvc_capture.name
        ):
            if self.exposure_mode == "auto":
                # special settings apply to both, Pupil Cam2 and Cam3
                special_settings = {200: 28, 180: 31}
                controls_dict = dict(
                    [(c.display_name, c) for c in self.uvc_capture.controls]
                )
                self.preferred_exposure_time = Exposure_Time(
                    max_ET=special_settings.get(self.frame_rate, 32),
                    frame_rate=self.frame_rate,
                    mode=self.exposure_mode,
                )

            try:
                controls_dict["Auto Exposure Priority"].value = 0
            except KeyError:
                pass

            try:
                controls_dict["Auto Exposure Mode"].value = 1
            except KeyError:
                pass

            try:
                controls_dict["Saturation"].value = 0
            except KeyError:
                pass

            try:
                controls_dict["Gamma"].value = 200
            except KeyError:
                pass

        else:
            self.uvc_capture.bandwidth_factor = 2.0
            try:
                controls_dict["Auto Focus"].value = 0
            except KeyError:
                pass

        # Restore session settings after setting defaults
        for c in self.uvc_capture.controls:
            try:
                c.value = uvc_controls[c.display_name]
            except KeyError:
                self.print(
                    'No UVC setting "{}" found from settings.'.format(c.display_name)
                )

        if self.should_check_stripes:
            self.stripe_detector = Check_Frame_Stripes()

        
    def recent_events(self):
        was_online = self.online

        frame = None

        try:
            frame = self.uvc_capture.get_frame(0.1)

            if np.isclose(frame.timestamp, 0):
                # sometimes (probably only on windows) after disconnections, the first frame has 0 ts
                self.print(
                    "Received frame with invalid timestamp."
                    " This can happen after a disconnect."
                    " Frame will be dropped!"
                )
                return

            if self.preferred_exposure_time:
                target = self.preferred_exposure_time.calculate_based_on_frame(frame)
                if target is not None:
                    self.exposure_time = target

            if self.stripe_detector and self.stripe_detector.require_restart(frame):
                # set the self.frame_rate in order to restart
                self.frame_rate = self.frame_rate
                self.print("Stripes detected")

        except uvc.StreamError:
            self._recent_frame = None
            self._restart_logic()
            return
        except (AttributeError, uvc.InitError):
            self._recent_frame = None
            time.sleep(0.02)
            self._restart_logic()
            return
        else:
            if self.ts_offset is not None:
                # c930 timestamps need to be set here. The camera does not provide valid pts from device
                frame.timestamp = uvc.get_time_monotonic() + self.ts_offset

            if self._last_ts is not None and frame.timestamp <= self._last_ts:
                self.print(
                    "Received non-monotonic timestamps from UVC! Dropping frame."
                    f" Last: {self._last_ts}, current: {frame.timestamp}"
                )
            else:
                self._last_ts = frame.timestamp
                # TODO <-----------------------------------
                # frame.timestamp -= self.g_pool.timebase.value
                # TODO <-----------------------------------
                self._recent_frame = frame
            self._restart_in = 3

            return frame

        # if was_online != self.online:
        #     self.update_menu()
    
    def recent_sample(self):
        frame = self.recent_events()
        if frame:
            return frame.gray, frame.timestamp, frame
        else:
            return

    def _restart_logic(self):
        if self._restart_in <= 0:
            if self.uvc_capture:
                self.print("Camera disconnected. Reconnecting...")
                self.name_backup = (self.uvc_capture.name,)
                self.backup_uvc_controls = self._get_uvc_controls()
                self.uvc_capture = None
            try:
                self._re_init_capture_by_names(
                    self.name_backup, self.backup_uvc_controls
                )
            except (InitialisationError, uvc.InitError):
                time.sleep(0.02)
            self._restart_in = int(5 / 0.02)
        else:
            self._restart_in -= 1


    def _re_init_capture_by_names(self, names, backup_uvc_controls={}):
        # burn-in test specific. Do not change text!
        self.devices.update()
        for d in self.devices:
            for name in names:
                if d["name"] == name:
                    self.print("Found device. {}.".format(name))
                    if self.uvc_capture:
                        self._re_init_capture(d["uid"])
                    else:
                        self._init_capture(d["uid"], backup_uvc_controls)
                    return
        raise InitialisationError(
            "Could not find Camera {} during re initilization.".format(names)
        )

    def _re_init_capture(self, uid):
        current_size = self.uvc_capture.frame_size
        current_fps = self.uvc_capture.frame_rate
        current_uvc_controls = self._get_uvc_controls()
        self.uvc_capture.close()
        self.uvc_capture = uvc.Capture(uid)
        self.configure_capture(current_size, current_fps, current_uvc_controls)
        # self.update_menu()

    def _init_capture(self, uid, backup_uvc_controls={}):
        self.uvc_capture = uvc.Capture(uid)
        self.configure_capture(
            self.frame_size_backup, self.frame_rate_backup, backup_uvc_controls
        )
        # self.update_menu()


    def _get_uvc_controls(self):
        d = {}
        if self.uvc_capture:
            for c in self.uvc_capture.controls:
                d[c.display_name] = c.value
        return d
    
    def print(self, msg):
        print(f'[{self.label}] {msg}')

    @property
    def name(self):
        if self.uvc_capture:
            return self.uvc_capture.name
        else:
            return "(disconnected)"

    @property
    def frame_size(self):
        if self.uvc_capture:
            return self.uvc_capture.frame_size
        else:
            return self.frame_size_backup

    @frame_size.setter
    def frame_size(self, new_size):
        # closest match for size
        sizes = [
            abs(r[0] - new_size[0]) + abs(r[1] - new_size[1])
            for r in self.uvc_capture.frame_sizes
        ]
        best_size_idx = sizes.index(min(sizes))
        size = self.uvc_capture.frame_sizes[best_size_idx]
        if tuple(size) != tuple(new_size):
            self.print(
                "{} resolution capture mode not available. Selected {}.".format(
                    new_size, size
                )
            )
        self.uvc_capture.frame_size = size
        self.frame_size_backup = size

        # self._intrinsics = Camera_Model.from_file(
        #     self.g_pool.user_dir, self.name, self.frame_size
        # )

        if self.should_check_stripes:
            self.stripe_detector = Check_Frame_Stripes()

    @property
    def frame_rate(self):
        if self.uvc_capture:
            return self.uvc_capture.frame_rate
        else:
            return self.frame_rate_backup

    @frame_rate.setter
    def frame_rate(self, new_rate):
        # closest match for rate
        rates = [abs(r - new_rate) for r in self.uvc_capture.frame_rates]
        best_rate_idx = rates.index(min(rates))
        rate = self.uvc_capture.frame_rates[best_rate_idx]
        if rate != new_rate:
            self.print(
                "{}fps capture mode not available at ({}) on '{}'. Selected {}fps. ".format(
                    new_rate, self.uvc_capture.frame_size, self.uvc_capture.name, rate
                )
            )
        self.uvc_capture.frame_rate = rate
        self.frame_rate_backup = rate

        if (
            "Pupil Cam2" in self.uvc_capture.name
            or "Pupil Cam3" in self.uvc_capture.name
        ):
            special_settings = {200: 28, 180: 31}
            if self.exposure_mode == "auto":
                self.preferred_exposure_time = Exposure_Time(
                    max_ET=special_settings.get(new_rate, 32),
                    frame_rate=new_rate,
                    mode=self.exposure_mode,
                )
            else:
                if self.exposure_time is not None:
                    self.exposure_time = min(
                        self.exposure_time, special_settings.get(new_rate, 32)
                    )

        if self.should_check_stripes:
            self.stripe_detector = Check_Frame_Stripes()
    
    @property
    def exposure_time(self):
        if self.uvc_capture:
            try:
                controls_dict = dict(
                    [(c.display_name, c) for c in self.uvc_capture.controls]
                )
                return controls_dict["Absolute Exposure Time"].value
            except KeyError:
                return None
        else:
            return self.exposure_time_backup

    @exposure_time.setter
    def exposure_time(self, new_et):
        try:
            controls_dict = dict(
                [(c.display_name, c) for c in self.uvc_capture.controls]
            )
            if abs(new_et - controls_dict["Absolute Exposure Time"].value) >= 1:
                controls_dict["Absolute Exposure Time"].value = new_et
        except KeyError:
            pass
    
    @property
    def jpeg_support(self):
        return True

    @property
    def online(self):
        return bool(self.uvc_capture)
    
    def cleanup(self):
        self.devices.cleanup()
        self.devices = None
        if self.uvc_capture:
            self.uvc_capture.close()
            self.uvc_capture = None
        super().cleanup()



