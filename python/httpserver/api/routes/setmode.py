from typing import List
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from base.controller import GeneralController


def onSetMode(controller: "GeneralController", params: List[str]):
    mode_str = params.get("mode")

    if mode_str is not None and len(mode_str) != 0:
        mode_str = mode_str[0]

    modes = controller.modes
    config = controller.config
    modeKeys = list(modes.keys())

    if mode_str not in modeKeys:
        return (400,
                {
                    "error": f"Invalid mode valid modes are {modeKeys}"
                })

    mode = modes[mode_str]
    required_vars = mode.data["required_vars"]

    if type(required_vars) is dict:
        usual_prefix = f"{mode_str}_"

        for key in required_vars.keys():
            param_key = key
            if key.startswith(usual_prefix):
                param_key = param_key.replace(usual_prefix, "")

            func = required_vars[key]["func"]
            res = func(params.get(param_key))
            res_keys = res.keys()

            if "error" in res_keys:
                return (400,
                        {
                            "error": res["error"]
                        })

            if "result" not in res_keys:
                return (500,
                        {
                            "error": f"Validate function mode {mode_str} with key {key} did not return any value"
                        })

            config.set(key, res["result"])
            print("Setting", key, "to", res["result"])

    config.setMode(mode_str)
    return (200, {
        "success": True,
        "mode": mode_str
    })
