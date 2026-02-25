def map_range(x, in_min, in_max, out_min, out_max):
    x = max(min(x, in_max), in_min)  # clamp
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
