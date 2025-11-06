# Copyright (c) 2025 Polymath Analytics. All rights reserved.
# Unauthorized copying of this file, via any medium is strictly prohibited.
# Proprietary and confidential.
# Written by Sven Steinbauer <<email>>.

import math
from shapely.geometry import mapping, base

import math
from shapely.geometry import mapping, base

def sanitize_obj(obj):
    """
    Recursively convert all numbers to Python float/int, replace NaN/Inf with None,
    convert Shapely geometries to GeoJSON dicts.
    """
    if obj is None:
        return None
    # Handle Shapely geometries
    if isinstance(obj, base.BaseGeometry):
        geo = mapping(obj)
        geo["coordinates"] = sanitize_obj(geo["coordinates"])
        return geo
    # Numbers
    if isinstance(obj, (float, int)):
        if not math.isfinite(obj):
            return None
        return float(obj)
    # NumPy numbers
    try:
        import numpy as np
        if isinstance(obj, (np.float64, np.float32, np.int64, np.int32)):
            val = float(obj)
            if not math.isfinite(val):
                return None
            return val
    except ImportError:
        pass
    # Dict
    if isinstance(obj, dict):
        return {k: sanitize_obj(v) for k, v in obj.items()}
    # List / tuple
    if isinstance(obj, (list, tuple)):
        return [sanitize_obj(x) for x in obj]
    # Other types (str, bool, etc.)
    return obj
