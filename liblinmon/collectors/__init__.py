from . import hwmon
from . import regulator
from . import rk_saradc
from . import devfreq
from . import clk
from . import cpufreq
from . import drm
from . import dmi
from . import wireless

registry = {
    "hwmon": hwmon.Collections(),
    "regulator": [regulator.Reg_Collection()],
    "rksaradc": rk_saradc.Collections(),
    "devfreq": devfreq.Collections(),
    "cpufreq": cpufreq.Collections(),
    "drm": drm.Collections(),
    "dmi": dmi.Collections(),
    "wireless": wireless.Collections(),
    }
