import filters.rainbow
import filters.normal
import filters.hex
import modes.visualization.visualization as visualization
import modes.full
import modes.stack
import modes.scanner

from tools.validators import validate_float, validate_int
from httpserver.currVars import getFilterMode


required_parsable = [ "min", "max", "type" ]

#! Make sure that requried vars are prefixed with root key (REQUIRED)
modes = {
    "scroll": {
        "func": visualization.visualize_scroll,
        "visualizer": True,
        "filters": True,
        "required_vars": {}
    },
    "spectrum": {
        "func": visualization.visualize_spectrum,
        "visualizer": True,
        "filters": True,
        "required_vars": {}
    },
    "energy": {
        "func": visualization.visualize_energy,
        "visualizer": True,
        "filters": True,
        "required_vars": {}
    },
    "full": {
        "func": modes.full.full,
        "visualizer": False,
        "filters": True,
        "required_vars": {}
    },
    "stack": {
        "func": modes.stack.stack,
        "visualizer": False,
        "filters": True,
        "required_vars": {
            "stack_concurrent": {
                "func": validate_int("concurrent", 1),
                "type": "int",
                "min": 1
            },
            "stack_speed": {
                "func": validate_float("speed"),
                "type": "float"
            }
        }
    },
    "scanner": {
        "func": modes.scanner.scanner,
        "visualizer": False,
        "filters": True,
        "required_vars": {
            "scanner_shadow": {
                "func": validate_int("shadow", 0),
                "type": "int",
                "min": 0
            },
            "scanner_size": {
                "func": validate_int("size", 1),
                "type": "int",
                "min": 1
            }
        }
    },
}
modeKeys = modes.keys()


rgb_index = 0


filters = {
    "hex": {
        "func": filters.hex.hex,
        "required_vars": {
            "hex_gradient": {
                "func": filters.hex.validateGradient,
                "type": "gradient"
            }
        }
    },
    "rainbow": {
        "func": filters.rainbow.rainbow,
        "required_vars": {
            "rainbow_speed": {
                "func": validate_float("speed"),
                "type": "float"
            }
        }
    },
    "normal": {
        "func": filters.normal.normal,
        "required_vars": {}
    }
}

def applyFilters(data):
    filter_mode = getFilterMode()
    curr_filter = filters[filter_mode]["func"]

    return curr_filter(data)
