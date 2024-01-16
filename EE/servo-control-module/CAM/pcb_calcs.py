import numpy as np
from pint import Quantity as Q

# PCB material properties
wt = Q(np.array([1, 1.5, 2, 3, 4, 5, 6, 7, 8, 9]), "oz")
thick = Q(
    np.array(
        [0.0348, 0.0522, 0.0696, 0.1044, 0.1392, 0.174, 0.2088, 0.2436, 0.2784, 0.3132]
    ),
    "mm",
)

# My PCB from Amazon
pcb_total_thick = Q(1.45, "mm")

# Cutter
tip_dia = Q(0.1, "mm")
v_angle = Q(60, "deg")

margin = 0.5  # [0-1], where 1=100% margin

# Setup
cu_weight_oz = 1

# Calculations
cu_weight_oz = Q(cu_weight_oz,'oz')
wt_idx = np.where(wt >= cu_weight_oz)[0][0]
cu_thick = thick[wt_idx] * (1 + margin)

# All cuts should be slightly deeper
cut_depth = pcb_total_thick + Q(0.2,'mm')

# Effective cutter diameter
eff_dia = tip_dia + 2 * cu_thick * np.tan(v_angle / 2)
eff_dia.ito("mm")

# Output
print(f"PCB copper wt : {cu_weight_oz:0.1fP}")
print(f"PCB copper th : {cu_thick:0.3f~P}  (with margin)")
print(f"Cutter tip dia: {tip_dia:0.2f~P}")
print(f"Cutter V-angle: {v_angle:0.1f~P}")
print(f"Cutting depth : {cu_thick:0.2f~P}")
print(f"Eff cutter dia: {eff_dia:0.2f~P}")
print(f"Drill/edge Z  : {-cut_depth:0.2f~P}")
