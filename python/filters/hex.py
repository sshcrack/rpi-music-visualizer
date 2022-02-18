from typing import List
from httpserver.currVars import getGradient
import numpy as np
from tools.gradient import calculateGradient
from httpserver.httpTypings import VerifierResult
import json

from tools.tools import isColorHex, hex_to_rgb

def hex(data):
    r, g, b = data

    gradient = getGradient()

    gradient_pixels = calculateGradient(len(r), gradient)

    for i in range(len(r)):
        maxVal = np.amax(np.array([r[i], g[i], b[i]]))
        d_r, d_g, d_b = np.array(gradient_pixels[i])

        r[i] = maxVal * d_r
        g[i] = maxVal * d_g
        b[i] = maxVal * d_b

    return np.array([ r, g, b])

def validateGradient(param: List[str]) -> VerifierResult:
    if param == None or len(param) == 0 or param[0] == None:
        return {
            "error": "Gradient param has to have a value",
            "result": None
        }

    param = param[0]
    data = json.loads(param)
    if type(data) is not list:
        return {
            "error": "Gradient has to be json and parsed has to be a list eg [[0, \#ff0000], [1, \#00ff37]]",
            "result": None
        }

    if len(data) < 1:
        return {
            "erorr": "Gradient has to have at least one step",
            "result": None
        }

    out = []
    has_one = False
    has_zero = False

    for el in data:
        if type(el) is not list:
            return {
                "error": "Gradient must only contain list elements.",
                "result": None
            }

        if len(el) != 2:
            return {
                "error": "List element has to have a length of 2",
                "result": None
            }
        
        step, curr_hex = el
        if type(step) is not float and type(step) is not int:
            return {
                "error" :"GradientElement[0] has to be a float",
                "result": None
            }

        if step < 0 or step > 1:
            return {
                "error": "GradientElement[0] has to be between 0 and 1",
                "result": None
            }

        if type(curr_hex) is not str:
            return {
                "error": "GradientElement[1] has to be a string",
                "result": None
            }

        if not isColorHex(curr_hex):
            return {
                "error": "GradientElement[1] has to be a hex",
                "result": None
            }

        if step == 0:
            has_zero = True

        if step == 1:
            has_one = True

        rgb = hex_to_rgb(curr_hex)
        out.append([ step, rgb ])

    if not has_zero:
        first = out[0][1]
        out.reverse()
        out.append([0, first])
        out.reverse()

    if not has_one:
        out.append([1, out[-1][1]])

    return {
        "result": out
    }