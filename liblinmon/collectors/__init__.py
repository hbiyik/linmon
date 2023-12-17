from . import hwmon
from . import regulator
from . import rk_saradc
from . import devfreq
from . import clk
from . import cpufreq

registry = {
    "hwmon": hwmon.Collections(),
    "regulator": [regulator.Reg_Collection()],
    "rksaradc": rk_saradc.Collections(),
    "devfreq": devfreq.Collections(),
    "cpufreq": cpufreq.Collections(),
    }
