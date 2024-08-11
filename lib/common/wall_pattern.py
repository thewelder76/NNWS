import math
from enum import Enum

from adsk.core import Matrix3D, ObjectCollection, Point3D, ValueInput, Vector3D
from adsk.fusion import (
    CircularPatternFeatureInput,
    Component,
    ExtrudeFeature,
    ExtrudeFeatureInput,
    FeatureOperations,
    MoveFeature,
    Occurrence,
    PatternDistanceType,
    RectangularPatternFeature,
    Sketch,
)

from ...lib import fusion360utils as futil
from ...lib.common.nnws_constants import GRIDFINITY_SIZE_CM
from ...lib.common.nnws_util import wrapInCollection

# Hex pattern, haven't tested anything else
WALL_NB_SIDES = 6


def circPatternSketch(targetOccurence: Occurrence, featureType: FeatureOperations, sketch: Sketch, extrudeHeight: float, patternCount: int, axis):
    profile = sketch.profiles.item(0)
    extrudes = targetOccurence.features.extrudeFeatures
    extrude_input: ExtrudeFeatureInput = extrudes.createInput(profile, featureType)
    extrude_distance = ValueInput.createByReal(extrudeHeight)
    extrude_input.setDistanceExtent(False, extrude_distance)
    extrude: ExtrudeFeature = extrudes.add(extrude_input)

    circularPatterns = targetOccurence.features.circularPatternFeatures
    circularPatternInput: CircularPatternFeatureInput = circularPatterns.createInput(wrapInCollection(extrude), axis)
    circularPatternInput.quantity = ValueInput.createByReal(patternCount)
    circularPatternInput.totalAngle = ValueInput.createByReal(math.pi * 2)
    circularPatternInput.isSymmetric = False
    circularPatterns.add(circularPatternInput)


def createDeltaVector(p1, p2):
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    dz = p2.z - p1.z
    return Vector3D.create(dx, dy, dz)


def calculateOffsetAngle(nbSides: int):
    return math.pi / 2 if nbSides % 2 == 0 else math.pi / nbSides + math.pi / 2


def createHexPoint(radius: float, index: int, offset: int, offset_angle: float) -> Point3D:
    # futil.log(f'offset angle: {offset_angle}')
    angle = 2 * math.pi * index / WALL_NB_SIDES + offset_angle
    x = math.cos(angle) * radius
    y = math.sin(angle) * radius
    # futil.log(f'angle: {angle}')
    if offset != 0:
        # futil.log(f'offset: {offset}')
        # futil.log(f'x: {x}')
        # futil.log(f'y: {y}')

        positiveOffset: bool = offset >= 0
        offsetValue = offset * GRIDFINITY_SIZE_CM
        # futil.log(f'offsetValue: {offsetValue}')
        new_x = x + offsetValue
        futil.log(f"new_x: {new_x}")
        hyp = math.hypot(y, new_x)
        # hyp = math.sqrt(y * y + new_x * new_x)

        # if not positiveOffset:
        #     hyp = -hyp
        futil.log(f"hyp: {hyp}")
        angle = math.asin(y / hyp)
        if not positiveOffset:
            angle = -angle
        futil.log(f"new angle: {angle}")

        x = math.cos(angle) * radius + offsetValue
        futil.log(f"final x: {x}")

    return Point3D.create(x, y, 0)


# pretty close!
# def createHexPoint(radius: float, index: int, offset: int, offset_angle: float)-> Point3D:
#     angle = 2 * math.pi * index / WALL_NB_SIDES + offset_angle
#     futil.log(f'angle: {angle}')
#     if offset == 0:
#         x = math.cos(angle) * radius
#         y = math.sin(angle) * radius
#     else:
#         futil.log(f'offset: {offset}')
#         x = math.cos(angle) * radius
#         y = math.sin(angle) * radius
#         futil.log(f'x: {x}')
#         futil.log(f'y: {y}')

#         new_x = x + offset * GRIDFINITY_SIZE_CM
#         futil.log(f'new_x: {new_x}')
#         hyp = math.sqrt(y * y / new_x * new_x)
#         futil.log(f'hyp: {hyp}')
#         angle = math.asin(y / hyp)
#         futil.log(f'new angle: {angle}')
#         # angle = 2 * math.pi * index / WALL_NB_SIDES + offset_angle
#         x = math.cos(angle) * radius + offset * GRIDFINITY_SIZE_CM
#         y = math.sin(angle) * radius

#     return Point3D.create(x, y, 0)


# This is based on the assumption that the hexagon is created in a counter clockwise direction with createExteriorContainer
class HexPointIndex(Enum):
    TOP = 0
    TOP_LEFT = 1
    BOTTOM_LEFT = 2
    BOTTOM = 3
    BOTTOM_RIGHT = 4
    TOP_RIGHT = 5


def patternBodies(rootComponent: Component, xAxis, bodies: ObjectCollection, width: int) -> RectangularPatternFeature:
    quantityOne = ValueInput.createByReal(width)
    distanceOne = ValueInput.createByReal(GRIDFINITY_SIZE_CM)

    # Generate a row of wall sections
    rectangularPatterns = rootComponent.features.rectangularPatternFeatures
    rectangularPatternInput = rectangularPatterns.createInput(bodies, xAxis, quantityOne, distanceOne, PatternDistanceType.SpacingPatternDistanceType)
    return rectangularPatterns.add(rectangularPatternInput)


def copyBodies(rootComponent: Component, bodies: ObjectCollection, toPoint: Vector3D) -> MoveFeature:
    transform = Matrix3D.create()
    transform.translation = toPoint
    moveFeature = rootComponent.features.moveFeatures
    moveFeatureInput = moveFeature.createInput2(bodies)
    moveFeatureInput.isGroup = True
    moveFeatureInput.transform = transform
    return moveFeature.add(moveFeatureInput)
