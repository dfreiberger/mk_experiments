#!/usr/bin/python
import hal, time, math
h = hal.component("sinvelo")
# h.newpin("in", hal.HALdd_FLOAT, hal.HAL_IN)
h.newpin("out", hal.HAL_FLOAT, hal.HAL_OUT)
h.ready()
t = 0.
interval = 0.1

try:
    while 1:
        t += interval
        time.sleep(interval)

        velo = math.sin(t) * 10.
        time.sleep(interval)
        h['out'] = velo

except KeyboardInterrupt:
    raise SystemExit
