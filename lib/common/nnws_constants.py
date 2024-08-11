from adsk.core import *


# Fusion works with cm, but I like define in mm, this is to convert the constants
def mmToCm(value):
    return value / 10


# Defaut axis for comparison
X_AXIS = Vector3D.create(1, 0, 0)
Y_AXIS = Vector3D.create(0, 1, 0)
Z_AXIS = Vector3D.create(0, 0, 1)

UNIT_MM = "mm"
UNIT_DEG = "°"

GRIDFINITY_SIZE_MM = 42
GRIDFINITY_SIZE_CM = mmToCm(GRIDFINITY_SIZE_MM)

# Screw tolerance/undersize to allow for rotation in mm
EXTERNAL_TOLERANCE_MM = 0.5
EXTERNAL_TOLERANCE_CM = mmToCm(EXTERNAL_TOLERANCE_MM)

# Screw head undersize, this is leave space between screws once on the wall
HEAD_OFFSET_MM = 3.5
HEAD_OFFSET_CM = mmToCm(HEAD_OFFSET_MM)

############################################
# Wall
############################################
# overall wall thickness
WALL_THICKNESS_MM = 8
WALL_THICKNESS_CM = mmToCm(WALL_THICKNESS_MM)

# bottom thinkness
WALL_BOTTOM_THICKNESS_MM = 1.5
WALL_BOTTOM_THICKNESS_CM = mmToCm(WALL_BOTTOM_THICKNESS_MM)

# Thikness of the outer wall
WALL_OUTER_WALL_THICKNESS_MM = 2
WALL_OUTER_WALL_THICKNESS_CM = mmToCm(WALL_OUTER_WALL_THICKNESS_MM)

# this is the distance between the outer wall interior section and the inner wall interio section
WALL_INNER_WALL_OFFSET_MM = 3.5
WALL_INNER_WALL_OFFSET_CM = mmToCm(WALL_INNER_WALL_OFFSET_MM)

WALL_INNER_SECTION_OFFSET_MM = 4
WALL_INNER_SECTION_OFFSET_CM = mmToCm(WALL_INNER_SECTION_OFFSET_MM)

NOTCH_SIZE_RADIUS_MM = 0.75
NOTCH_SIZE_RADIUS_CM = mmToCm(NOTCH_SIZE_RADIUS_MM)

# TODO change to radians
INTERNAL_WALL_CHAMFER_ANGLE = 75

################################################
# Gridfinity base generator Add-in integration
################################################
GRIDFINITY_Z_OFFSET_MM = 0.5
GRIDFINITY_Z_OFFSET_CM = mmToCm(GRIDFINITY_Z_OFFSET_MM)

# from top to bottom
GRIDFINITY_BASE_HEIGHT_MM = 10.4 + 0.5
GRIDFINITY_BASE_HEIGHT_CM = mmToCm(GRIDFINITY_BASE_HEIGHT_MM)

############################################
# Accessories
############################################
THREAD_SIZE_D_MAJOR_MM = 38
THREAD_SIZE_D_MAJOR_CM = mmToCm(THREAD_SIZE_D_MAJOR_MM)

# Thread pitch in mm
THREAD_PITCH_MM = 2.5
THREAD_PITCH_CM = mmToCm(THREAD_PITCH_MM)

# I don't remember how I ended up with this value, but it works
H_NEW_MM = 0.75 * 0.75 * THREAD_PITCH_MM
H_NEW_CM = mmToCm(H_NEW_MM)

# Thread radius, this is the radius of the thread
THREAD_RADIUS_MM = 0.275 * THREAD_PITCH_MM
THREAD_RADIUS_CM = mmToCm(THREAD_RADIUS_MM)

# Main Screw Body Clearance
MAIN_SCREW_BODY_CLEARANCE_MM = 0.1
MAIN_SCREW_BODY_CLEARANCE_CM = mmToCm(MAIN_SCREW_BODY_CLEARANCE_MM)

# Main Screw Body End Clearance
MAIN_SCREW_BODY_END_CLEARANCE_MM = 0.5
MAIN_SCREW_BODY_END_CLEARANCE_CM = mmToCm(MAIN_SCREW_BODY_END_CLEARANCE_MM)

MAIN_SCREW_HEAD_THICKNESS_MM = 4
MAIN_SCREW_HEAD_THICKNESS_CM = mmToCm(MAIN_SCREW_HEAD_THICKNESS_MM)

MAIN_SCREW_HEIGHT_MM = WALL_THICKNESS_MM + MAIN_SCREW_HEAD_THICKNESS_MM - WALL_BOTTOM_THICKNESS_MM
MAIN_SCREW_HEIGHT_CM = mmToCm(MAIN_SCREW_HEIGHT_MM)

MAIN_SCREW_THREAD_BODY_THICKNESS_MM = 2
MAIN_SCREW_THREAD_BODY_THICKNESS_CM = mmToCm(MAIN_SCREW_THREAD_BODY_THICKNESS_MM)

MAIN_SCREW_HEAD_INTERNAL_DIAMETER_MM = 26
MAIN_SCREW_HEAD_INTERNAL_DIAMETER_CM = mmToCm(MAIN_SCREW_HEAD_INTERNAL_DIAMETER_MM)

ACC_EXTRA_SPACING_DEFAULT_MM = 7.5
ACC_EXTRA_SPACING_DEFAULT_CM = mmToCm(ACC_EXTRA_SPACING_DEFAULT_MM)

############################################
# Shelf
############################################
MIN_SHELF_THICKNESS_MM = 3
MIN_SHELF_THICKNESS_CM = mmToCm(MIN_SHELF_THICKNESS_MM)

MIN_SHELF_SIZE_MM = 12
MIN_SHELF_SIZE_CM = mmToCm(MIN_SHELF_SIZE_MM)

ACC_EXTENSION_HEIGTH_CM = GRIDFINITY_BASE_HEIGHT_CM
ACC_EXTENSION_WIDTH_CM = GRIDFINITY_BASE_HEIGHT_CM

ACC_INTERNAL_SKETCH_RADIUS_MM = 1
ACC_INTERNAL_SKETCH_RADIUS_CM = mmToCm(ACC_INTERNAL_SKETCH_RADIUS_MM)

ACC_SHELF_WIDTH_MM = 6.5
ACC_SHELF_WIDTH_CM = mmToCm(ACC_SHELF_WIDTH_MM)

ACC_LEDGER_WIDTH_MM = 4
ACC_LEDGER_WIDTH_CM = mmToCm(ACC_LEDGER_WIDTH_MM)

ACC_ANCHOR_TOP_OFFSET_MM = 0.5
ACC_ANCHOR_TOP_OFFSET_CM = mmToCm(ACC_ANCHOR_TOP_OFFSET_MM)

# STL creation automation
CALLBACK_NAME = "scriptGenerateWall"
