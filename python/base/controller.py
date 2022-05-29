from typing import Any, Dict

from time import time

import numpy as np

import config
from base.hardware.configDict import loadDeviceConfig
from httpserver.api.apiServer import APIServer
from tools.interfaces import find_free_port
from tools.nparray import multipleIntArr
from base.visualization.dsp import ExpFilter
from tools.fps import frames_per_second
from base.configManager import ConfigManager
from tools.energyspeed import getAvgEnergy
import base.visualization.microphone as microphone
from tools.timer import Timer
from tools.tools import clamp
from base.hardware.GUIManager import GUIManager
from base.hardware.LEDManager import LEDManager
from base.modes.full import FullMode
from base.filters.hex import HexFilter
from base.filters.normal import NormalMode
from base.GeneralMode import GeneralMode
from base.GeneralFilter import GeneralFilter
from base.filters.rainbow import RainbowMode

defaultMode = "normal"
defaultFilter = "full"

defaultModes = {
    "full": FullMode
}

defaultFilters = {
    "hex": HexFilter,
    "normal": NormalMode,
    "rainbow": RainbowMode
}


class GeneralController:
    config: ConfigManager
    api: APIServer
    deviceId: str
    timer = Timer()
    initialized = False
    modes: Dict[str, GeneralMode] = {}
    filters: Dict[str, GeneralFilter] = {}

    energy_filter: ExpFilter

    def __init__(self, deviceId: str, modes: Dict[str, Any], filters: Dict[str, Any], configDefaults=None, gui=False):
        if configDefaults is None:
            configDefaults = {}

        self.deviceId = deviceId
        self.device = loadDeviceConfig(deviceId)
        self.config = ConfigManager(deviceId, configDefaults)
        self.enabled = self.device.enabled

        if not microphone.isRunning():
            print("Starting microphone service...")
            microphone.start()

        self.energySense = clamp(0.0001, self.config.get("energy_sensitivity", .99), .99)
        self.isEnergySpeed = self.config.get("energy_speed", False)
        self.isEnergyBrightness = self.config.get("energy_brightness", False)
        self.energyBrightnessMult = self.config.get("energy_brightness_mult", 1)

        self.energy_filter = ExpFilter(
            1,
            alpha_decay=self.energySense,
            alpha_rise=.99
        )

        self.constructorModes = {**defaultModes, **modes}
        self.constructorFilters = {**defaultFilters, **filters}

        for keyMode in list(self.constructorModes.keys()):
            self.modes[keyMode] = self.constructorModes[keyMode](self)

        for keyFilter in list(self.constructorFilters.keys()):
            self.filters[keyFilter] = self.constructorFilters[keyFilter](self)

        self.pixels = np.tile(1, (3, self.device.N_PIXELS))

        self.currMode = defaultMode
        self.currFilter = defaultFilter
        # How far to enable animation state has proceeded. 1 = normal, 0 = off
        self.currEnableAnimationState = 1.0
        self.prev_fps_update = time()

        try:
            self.led = LEDManager(self.device)
        except ImportError as e:
            print(f"Could not load LEDManager. Disabling leds.")
            print(e)
            self.led = None

        if gui:
            try:
                self.gui = GUIManager(self.device, deviceId)
            except Exception as e:
                print(f"Could not start GUI Manager. Disabling...")
                print(e)
                self.gui = None

        if self.gui is None and self.led is None:
            raise ValueError("Neither GUI nor LEDS could be loaded. Stopping.")

        self.api = APIServer(self)
        self.api.serveThreaded("127.0.0.1", find_free_port())

    def shutdown(self):
        print("Shutting down with id", self.deviceId)
        microphone.stop()
        self.config.save()

    def updateVars(self):
        self.energySense = self.config.get("energy_sensitivity", .99)
        self.isEnergySpeed = self.config.get("energy_speed", False)
        self.isEnergyBrightness = self.config.get("energy_brightness", False)
        self.energyBrightnessMult = self.config.get("energy_brightness_mult", 1)

    def run(self):
        if round(time()) % 3 == 0:
            self.updateVars()
        if not self.enabled and self.currEnableAnimationState == 0:
            self.pixels *= 0
            self.updateLeds()

            self.timer.update()
            return

        isVisualizer, useFilters, filterFunc, modeFunc = self.getCurr()

        energy, outPixels = self.calculateModePixels(isVisualizer, modeFunc)
        if useFilters:
            outPixels = filterFunc(outPixels)
            if energy is not None and self.isEnergyBrightness:
                outPixels = self.calculateEnergyBrightness(outPixels, energy)

        outPixels = self.applyEnableAnimation(outPixels)
        self.pixels = outPixels
        self.updateLeds()

        if config.DISPLAY_FPS:
            fps = frames_per_second()
            if time() - 0.5 > self.prev_fps_update:
                self.prev_fps_update = time()
                print("Dev" + self.deviceId + ' FPS {:.0f} / {:.0f}'.format(fps, config.FPS))

    def updateLeds(self):
        if self.led is not None:
            self.led.update(self.pixels)
        if self.gui is not None:
            self.gui.update(self.pixels)
            if self.gui.exitSignal:
                raise Exception("Exit by GUI")

    def applyEnableAnimation(self, outPixels: np.ndarray):
        delta = self.timer.getDelta()
        animState = self.currEnableAnimationState

        if self.enabled and animState < 1:
            outPixels = multipleIntArr(outPixels, animState)
            animState = min(animState + delta * 8, 1)
        elif not self.enabled and animState > 0:
            outPixels = multipleIntArr(outPixels, animState)
            animState = max(0, animState - delta * 3)

        self.currEnableAnimationState = animState
        return outPixels

    def calculateEnergyBrightness(self, outPixels: np.ndarray, energy: float):
        return multipleIntArr(outPixels, energy * self.energyBrightnessMult)

    def calculateModePixels(self, isVisualizer: bool, modeFunc):
        energy = None
        modePixelsOut = None

        shouldReadMicrophone = isVisualizer or self.isEnergyBrightness or self.isEnergySpeed
        if shouldReadMicrophone:
            raw = microphone.read()
            mel = microphone.microphone_update(raw)
            if isVisualizer:
                modePixelsOut = modeFunc(mel, self)
            else:
                avgEnergy = getAvgEnergy(mel)
                energy = self.energy_filter.update(avgEnergy)
                self.config.set("energy_curr", energy)

        if not isVisualizer:
            modePixelsOut = modeFunc(None, self)
        self.timer.update()

        return energy, modePixelsOut

    def setEnabled(self, enabled):
        self.enabled = enabled
        self.device.enabled = enabled

    def getCurr(self):
        modeClass = self.modes[self.currMode]
        filterClass = self.filters[self.currFilter]

        if modeClass is None:
            modeClass = self.modes[defaultMode]
        if filterClass is None:
            filterClass = self.filters[defaultFilter]

        modeData = modeClass.data
        isVisualizer = modeData["visualizer"]
        useFilters = modeData["filters"]
        return (
            isVisualizer,
            useFilters,
            lambda data: filterClass.run(data),
            lambda mel: modeClass.run(mel)
        )
