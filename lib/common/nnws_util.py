import math

from adsk.core import Appearance, Application, Color, ColorProperty, GroupCommandInput, Matrix3D, ObjectCollection, Point3D, SurfaceTypes, ValueCommandInput, ValueInput, Vector3D
from adsk.fusion import (
    BRepEdges,
    BRepFace,
    BRepFaces,
    ChamferFeature,
    Component,
    ConstructionPlane,
    ConstructionPlaneInput,
    Design,
    ExtrudeFeature,
    ExtrudeFeatures,
    FeatureOperations,
    FilletFeature,
    FilletFeatureInput,
    FilletFeatures,
    Occurrence,
    Occurrences,
    Sketch,
    SweepFeature,
)

from ...lib import fusion360utils as futil

# NNWS constants
from ...lib.common.nnws_constants import INTERNAL_WALL_CHAMFER_ANGLE, THREAD_PITCH_CM, THREAD_RADIUS_CM, UNIT_DEG, X_AXIS, Y_AXIS, Z_AXIS

# NNWS constants


def valueInputMinMax(group: GroupCommandInput, id: str, text: str, unitType: str, value: float, min: float, max: float = -1) -> ValueCommandInput:
    """
    Creates a ValueCommandInput with minimum and maximum values.

    Args:
        group (GroupCommandInput): The parent group command input.
        id (str): The ID of the value input.
        text (str): The display text of the value input.
        unitType (str): The unit type of the value input.
        value (float): The initial value of the value input.
        min (float): The minimum value of the value input.
        max (float, optional): The maximum value of the value input. Defaults to -1.

    Returns:
        ValueCommandInput: The created value command input.
    """
    valueInput = ValueInput.createByReal(math.radians(value)) if unitType == UNIT_DEG else ValueInput.createByReal(value)
    input = group.children.addValueInput(id, text, unitType, valueInput)
    input.minimumValue = math.radians(min) if unitType == UNIT_DEG else min
    if max > 0:
        input.maximumValue = math.radians(max) if unitType == UNIT_DEG else max
    return input


def createNamedComponent(root: Component, name: str) -> Occurrence:
    """
    Creates a named component within the root component.

    Args:
        root (Component): The root component.
        name (str): The name of the new component.

    Returns:
        Occurrence: The created occurrence of the new component.
    """
    newComponent = Occurrences.cast(root.occurrences).addNewComponent(Matrix3D.create())
    newComponent.component.name = name
    newComponent.activate()
    return newComponent


def commonCreateThread(targetOccurence: Occurrence, threadStartOffset: float, radius: float, height: float) -> SweepFeature:
    """
    Creates a thread feature on a given target occurrence.
    This is the common code used by the external and internal thread creation functions.

    Args:
        targetOccurence (Occurrence): The target occurrence on which the thread feature will be created.
        threadStartOffset (float): The offset of the thread start from the origin.
        radius (float): The radius of the thread.
        height (float): The height of the thread.

    Returns:
        SweepFeature: The created thread feature.
    """
    threadRadius = THREAD_RADIUS_CM
    sketches = targetOccurence.sketches
    xy_plane = targetOccurence.xYConstructionPlane
    sketch = sketches.add(xy_plane)

    # number of points per revolution
    # 360 / 15 = 24, so 24 points will be created per revolution, whith a pitch of 2.5mm
    resolution = 360 / 15
    revolutions = height / THREAD_PITCH_CM

    # first point inside the bottom to have a smooth transition
    splineBottom = Point3D.create(radius, 0, threadStartOffset)
    points = ObjectCollection.create()
    points.add(splineBottom)

    pointIndex = 1
    iteration = int(resolution * revolutions)
    for pointIndex in range(1, iteration):
        points.add(helix_point(threadStartOffset, radius, THREAD_PITCH_CM, resolution, pointIndex))

    spline = sketch.sketchCurves.sketchFittedSplines.add(points)
    spline.name = "ThreadSpline"

    # Create the sketch for the thread profile for the sweep, creating in the xz plane so the sweep is following the helix
    xz_plane = targetOccurence.xZConstructionPlane
    sketch = sketches.add(xz_plane)

    # This is the circle for the thread profile
    sketchProfile = Point3D.create(radius, -threadStartOffset, 0)
    sketch.sketchCurves.sketchCircles.addByCenterRadius(sketchProfile, threadRadius)

    sweep = targetOccurence.features.sweepFeatures
    path = targetOccurence.features.createPath(spline)

    # with JoinFeatureOperation , fillet can be added with the thread and the cilinder body
    sweepInput = sweep.createInput(sketch.profiles.item(0), path, FeatureOperations.JoinFeatureOperation)
    sweepFeature: SweepFeature = sweep.add(sweepInput)
    sweepFeature.name = "Thread"

    return sweepFeature


def createExternalThread(targetOccurence: Occurrence, threadStartOffset: float, radius: float, height: float) -> SweepFeature:
    """
    Creates an external thread feature on a target occurrence.

    Args:
        targetOccurence (Occurrence): The target occurrence on which the thread will be created.
        threadStartOffset (float): The offset from the start of the thread.
        radius (float): The radius of the thread.
        height (float): The height of the thread.

    Returns:
        SweepFeature: The created external thread feature.
    """

    sweepFeature = commonCreateThread(targetOccurence, threadStartOffset, radius, height)

    edgeCollection = ObjectCollection.create()
    for edge in sweepFeature.faces.item(0).edges:
        # 2 long edges over 30cm are the ones connecting the thread to the cilinder
        if edge.length > 30:
            edgeCollection.add(edge)

    filletEdges(targetOccurence, edgeCollection, 0.075)

    return sweepFeature


def createInternalThread(targetOccurence: Occurrence, threadStartOffset: float, radius: float, height: float) -> SweepFeature:
    """
    Creates an internal thread feature on the target occurrence.

    Args:
        targetOccurence (Occurrence): The target occurrence to create the thread on.
        threadStartOffset (float): The offset of the thread start.
        radius (float): The radius of the thread.
        height (float): The height of the thread.

    Returns:
        SweepFeature: The created internal thread feature.
    """

    sweepFeature = commonCreateThread(targetOccurence, threadStartOffset, radius, height)

    # TODO need better selection that that! At least area and edge selcetion should be based on contants calculation of expected values
    # Filet the thread end
    endEdgeCollection = ObjectCollection.create()
    for f in sweepFeature.faces:
        if f.area > 10:
            for edge in f.edges:
                if edge.length < 5:
                    endEdgeCollection.add(edge)

    filletEdges(targetOccurence, endEdgeCollection, 0.05)

    edgeCollection = ObjectCollection.create()
    for f in sweepFeature.faces:
        if f.area > 10:
            for edge in f.edges:
                if edge.length > 15:
                    edgeCollection.add(edge)

    filletEdges(targetOccurence, edgeCollection, 0.075)

    return sweepFeature


def filletEdges(targetOccurence: Occurrence, edgeCollection: ObjectCollection, radius: float) -> FilletFeature:
    """
    Fillets the edges in the given edge collection with the specified radius.

    Args:
        targetOccurence (Occurrence): The occurrence containing the edges to be filleted.
        edgeCollection (ObjectCollection): The collection of edges to be filleted.
        radius (float): The radius of the fillet.

    Returns:
        FilletFeature: The fillet feature created.
    """
    fillet: FilletFeatures = targetOccurence.features.filletFeatures
    filletInput: FilletFeatureInput = fillet.createInput()
    filletInput.addConstantRadiusEdgeSet(edgeCollection, ValueInput.createByReal(radius), True)
    return fillet.add(filletInput)


def wrapInCollection(object: any) -> ObjectCollection:
    """
    Wraps a single object in a collection.

    Args:
        object: The object to be wrapped in a collection.

    Returns:
        ObjectCollection: A collection containing the input object.
    """
    collection = ObjectCollection.create()
    collection.add(object)
    return collection


def calculateChamferWidth(chamferAngle: float, chamferHeight: float) -> float:
    """
    Calculates the width of a chamfer given the chamfer angle and height.

    Args:
        chamferAngle (float): The angle of the chamfer in degrees.
        chamferHeight (float): The height of the chamfer.

    Returns:
        float: The width of the chamfer.
    """
    return chamferHeight / math.tan(math.radians(chamferAngle))


def createAnchorChamfer(targetOccurence: Occurrence, edge: BRepEdges, chamferHeight: float, isFlipped: bool = False) -> ChamferFeature:
    """
    Creates a chamfer feature on the specified edge of the target occurrence.

    Args:
        targetOccurence (Occurrence): The target occurrence on which the chamfer feature will be created.
        edge (BRepEdges): The edge on which the chamfer feature will be created.
        chamferHeight (float): The height of the chamfer.
        isFlipped (bool, optional): Specifies whether the chamfer is flipped. Defaults to False.

    Returns:
        ChamferFeature: The created chamfer feature.
    """

    rad = math.radians(INTERNAL_WALL_CHAMFER_ANGLE)
    internalChamferWidth = calculateChamferWidth(INTERNAL_WALL_CHAMFER_ANGLE, chamferHeight)

    chamfers = targetOccurence.component.features.chamferFeatures
    chamferInput = chamfers.createInput2()
    chamferInput.chamferEdgeSets.addDistanceAndAngleChamferEdgeSet(
        wrapInCollection(edge), ValueInput.createByReal(internalChamferWidth), ValueInput.createByReal(rad), isFlipped, True
    )
    return chamfers.add(chamferInput)


def isFaceParallelTo(face: BRepFace, axis: Vector3D) -> bool:
    """
    Checks if a face is parallel to a given axis.

    Args:
        face (BRepFace): The face to check.
        axis (Vector3D): The axis to check against.

    Returns:
        bool: True if the face is parallel to the axis, False otherwise.
    """
    return hasattr(face.geometry, "normal") and face.geometry.normal.isParallelTo(axis)


def selectTopFace(component: Component, plane: ConstructionPlane) -> BRepFace:
    """
    Selects the top face of a component based on a given construction plane.

    Args:
        component (Component): The component to select the top face from.
        plane (ConstructionPlane): The construction plane used for reference.

    Returns:
        BRepFace: The top face of the component or None.
    """
    topFace = None
    top = 0
    for b in component.bRepBodies:
        for f in b.faces:
            pointOnFace = 0
            if plane.geometry.normal.isParallelTo(X_AXIS) and isFaceParallelTo(f, X_AXIS):
                pointOnFace = f.pointOnFace.x
            elif plane.geometry.normal.isParallelTo(Y_AXIS) and isFaceParallelTo(f, Y_AXIS):
                pointOnFace = f.pointOnFace.y
            elif plane.geometry.normal.isParallelTo(Z_AXIS) and isFaceParallelTo(f, Z_AXIS):
                pointOnFace = f.pointOnFace.z

            if abs(pointOnFace) > abs(top):
                top = pointOnFace
                topFace = f
    return topFace


def selectFaceAt(component: Component, plane: ConstructionPlane, z: float) -> BRepFace:
    """
    Selects a face from a given component that lies on a specified construction plane at a given z-coordinate.

    Args:
        component (Component): The component to search for faces.
        plane (ConstructionPlane): The construction plane to check for face alignment.
        z (float): The z-coordinate of the desired face.

    Returns:
        BRepFace: The selected face if found, None otherwise.
    """
    for b in component.bRepBodies:
        for f in b.faces:
            pointOnFace = 0
            if plane.geometry.normal.isParallelTo(X_AXIS) and isFaceParallelTo(f, X_AXIS):
                pointOnFace = f.pointOnFace.x
            elif plane.geometry.normal.isParallelTo(Y_AXIS) and isFaceParallelTo(f, Y_AXIS):
                pointOnFace = f.pointOnFace.y
            elif plane.geometry.normal.isParallelTo(Z_AXIS) and isFaceParallelTo(f, Z_AXIS):
                pointOnFace = f.pointOnFace.z

            if math.isclose(pointOnFace, z, abs_tol=0.01):
                return f
    return None


def createOffsetPlane(target: Occurrence, onFace: BRepFace, offsetVal: float) -> ConstructionPlane:
    """
    Creates an offset plane from a given face on a target occurrence.

    Args:
        target (Occurrence): The target occurrence.
        onFace (BRepFace): The face to offset from.
        offsetVal (float): The offset value.

    Returns:
        ConstructionPlane: The created offset plane.
    """
    planes = target.component.constructionPlanes
    planeInput: ConstructionPlaneInput = planes.createInput()
    planeInput.setByOffset(onFace, ValueInput.createByReal(offsetVal))
    offsetPlane = planes.add(planeInput)
    return offsetPlane


def createCylinder(targetOccurence: Occurrence, outerRadius: float, height: float, zOffset=0.0) -> ExtrudeFeatures:
    """
    Creates a cylinder in the specified target occurrence with the given outer radius, height, and z-offset.

    Parameters:
        targetOccurence (Occurrence): The target occurrence where the cylinder will be created.
        outerRadius (float): The outer radius of the cylinder.
        height (float): The height of the cylinder.
        zOffset (float, optional): The z-offset of the cylinder. Defaults to 0.0.

    Returns:
        ExtrudeFeatures: The extrude features of the created cylinder.
    """
    return createCylinderFromPointXYPlane(targetOccurence, outerRadius, height, Point3D.create(0, 0, zOffset))


def createCylinderFromPointXYPlane(
    targetOccurence: Occurrence, outerRadius: float, height: float, point3d: Point3D, operationType: FeatureOperations = FeatureOperations.JoinFeatureOperation
) -> ExtrudeFeatures:
    """
    Creates a cylinder from a point in the XY plane.

    Args:
        targetOccurence (Occurrence): The target occurrence to create the cylinder in.
        outerRadius (float): The outer radius of the cylinder.
        height (float): The height of the cylinder.
        point3d (Point3D): The point in the XY plane where the cylinder will be created.
        operationType (FeatureOperations, optional): The operation type for the cylinder creation. Defaults to FeatureOperations.JoinFeatureOperation.

    Returns:
        ExtrudeFeatures: The created cylinder feature.
    """
    return createCylinderFromPoint(targetOccurence, outerRadius, height, point3d, targetOccurence.xYConstructionPlane, operationType)


def createCylinderFromPointXZPlane(
    targetOccurence: Occurrence, outerRadius: float, height: float, point3d: Point3D, operationType: FeatureOperations = FeatureOperations.JoinFeatureOperation
) -> ExtrudeFeatures:
    """
    Creates a cylinder from a point on the XZ plane.

    Args:
        targetOccurence (Occurrence): The target occurrence to create the cylinder in.
        outerRadius (float): The outer radius of the cylinder.
        height (float): The height of the cylinder.
        point3d (Point3D): The point on the XZ plane to create the cylinder from.
        operationType (FeatureOperations, optional): The operation type for the cylinder creation. Defaults to FeatureOperations.JoinFeatureOperation.

    Returns:
        ExtrudeFeatures: The created cylinder as an ExtrudeFeatures object.
    """
    return createCylinderFromPoint(targetOccurence, outerRadius, height, point3d, targetOccurence.xZConstructionPlane, operationType)


def createCylinderFromPoint(
    targetOccurence: Occurrence, outerRadius: float, height: float, point3d: Point3D, plane, operationType: FeatureOperations = FeatureOperations.JoinFeatureOperation
) -> ExtrudeFeatures:
    """
    Creates a cylinder feature by extruding a circle sketch from a given point.

    Args:
        targetOccurence (Occurrence): The target occurrence where the cylinder will be created.
        outerRadius (float): The outer radius of the cylinder.
        height (float): The height of the cylinder.
        point3d (Point3D): The center point of the circle sketch.
        plane: The plane on which the circle sketch will be created.
        operationType (FeatureOperations, optional): The type of operation to perform. Defaults to FeatureOperations.JoinFeatureOperation.

    Returns:
        ExtrudeFeatures: The created extrude feature representing the cylinder.
    """

    sketches = targetOccurence.sketches
    outer_sketch = sketches.add(plane)
    outer_sketch.sketchCurves.sketchCircles.addByCenterRadius(point3d, outerRadius)
    profile = outer_sketch.profiles.item(0)

    extrudes = targetOccurence.features.extrudeFeatures
    extrude_input = extrudes.createInput(profile, operationType)
    extrude_distance = ValueInput.createByReal(height)
    extrude_input.setDistanceExtent(False, extrude_distance)
    return extrudes.add(extrude_input)


def create2PointRectFromPoints(
    targetOccurence: Occurrence, sketch: Sketch, p1: Point3D, p2: Point3D, extrudeHeight: float, operationType: FeatureOperations = FeatureOperations.JoinFeatureOperation
) -> ExtrudeFeature:
    """
    Creates a 2-point rectangle in the given sketch using the provided points.
    Extrudes the rectangle to the specified height and returns the resulting extrude feature.

    Args:
        targetOccurence (Occurrence): The target occurrence where the extrude feature will be created.
        sketch (Sketch): The sketch where the rectangle will be drawn.
        p1 (Point3D): The first point of the rectangle.
        p2 (Point3D): The second point of the rectangle.
        extrudeHeight (float): The height of the extrude.
        operationType (FeatureOperations, optional): The type of operation to perform during the extrude. Defaults to FeatureOperations.JoinFeatureOperation.

    Returns:
        ExtrudeFeature: The resulting extrude feature.

    """
    sketch.sketchCurves.sketchLines.addTwoPointRectangle(p1, p2)
    profile = sketch.profiles.item(0)
    extrudes = targetOccurence.component.features.extrudeFeatures
    extrude_input = extrudes.createInput(profile, operationType)
    extrude_distance = ValueInput.createByReal(extrudeHeight)
    extrude_input.setDistanceExtent(False, extrude_distance)
    return extrudes.add(extrude_input)


def createHollowCylinder(targetOccurence: Occurrence, outerRadius: float, offset: float, height: float) -> ExtrudeFeatures:
    """
    Creates a hollow cylinder by extruding two concentric circles.

    Args:
        targetOccurence (Occurrence): The target occurrence to create the cylinder in.
        outerRadius (float): The radius of the outer circle.
        offset (float): The offset between the outer and inner circles.
        height (float): The height of the cylinder.

    Returns:
        ExtrudeFeatures: The extrude feature representing the hollow cylinder.
    """

    sketches = targetOccurence.sketches
    xy_plane = targetOccurence.xYConstructionPlane

    # Create a sketch for the outer circle
    outer_sketch = sketches.add(xy_plane)
    outer_sketch.sketchCurves.sketchCircles.addByCenterRadius(Point3D.create(0, 0, 0), outerRadius)

    # Create a second sketch for the inner circle
    inner_sketch = sketches.add(xy_plane)
    inner_sketch.sketchCurves.sketchCircles.addByCenterRadius(Point3D.create(0, 0, 0), outerRadius - offset)

    # Create an extrusion for the cylinder
    extrudes = targetOccurence.features.extrudeFeatures
    extrude_input = extrudes.createInput(outer_sketch.profiles.item(0), FeatureOperations.NewBodyFeatureOperation)
    extrude_distance = ValueInput.createByReal(height)
    extrude_input.setDistanceExtent(False, extrude_distance)
    extrudes.add(extrude_input)

    # Create a second extrusion to remove material and create the hole
    hole_extrude_input = extrudes.createInput(inner_sketch.profiles.item(0), FeatureOperations.CutFeatureOperation)
    hole_extrude_input.setDistanceExtent(False, extrude_distance)
    return extrudes.add(hole_extrude_input)


def helix_point(zOffset: float, radius: float, pitch: float, resolution: int, pointIndex: int) -> Point3D:
    """
    Calculates the coordinates of a point on a helix.

    Args:
        zOffset (float): The offset along the z-axis
        radius (float): The radius of the helix.
        pitch (float): The distance between each loop of the helix.
        resolution (int): The number of points used to approximate the helix.
        pointIndex (int): The index of the point on the helix.

    Returns:
        Point3D: The coordinates of the point on the helix.
    """
    x = radius * math.cos(2 * math.pi * pointIndex / resolution)
    y = radius * math.sin(2 * math.pi * pointIndex / resolution)
    z = pitch * pointIndex / resolution + zOffset

    return Point3D.create(x, y, z)


def displayFaces(name: str, faces: BRepFaces):
    futil.log(f"{name} has {faces.count} faces")
    for face in faces:
        futil.log(f"{face}")
        futil.log(f"{face.geometry.surfaceType}")


def getColorForFace(face: BRepFace) -> Appearance:
    if face.geometry.surfaceType == SurfaceTypes.PlaneSurfaceType:  # 0
        return getColor(255, 0, 0)  # red
    elif face.geometry.surfaceType == SurfaceTypes.CylinderSurfaceType:  # 1
        return getColor(0, 0, 255)  # blue
    elif face.geometry.surfaceType == SurfaceTypes.ConeSurfaceType:  # 2
        return getColor(255, 0, 255)  # magenta
    elif face.geometry.surfaceType == SurfaceTypes.SphereSurfaceType:  # 3
        return getColor(0, 255, 255)  # cyan
    elif face.geometry.surfaceType == SurfaceTypes.TorusSurfaceType:  # 4
        return getColor(0, 0, 140)  # navy
    elif face.geometry.surfaceType == SurfaceTypes.EllipticalCylinderSurfaceType:  # 5
        return getColor(128, 0, 0)  # maroon
    elif face.geometry.surfaceType == SurfaceTypes.EllipticalConeSurfaceType:  # 6
        return getColor(0, 255, 0)  # green
    elif face.geometry.surfaceType == SurfaceTypes.NurbsSurfaceType:  # 7
        return getColor(255, 255, 255)  # white
    else:
        return getColor(255, 255, 0)


def getColor(r, g, b) -> Appearance:
    app = Application.get()
    name = "RGB: {}, {}, {}".format(r, g, b)
    try:
        color = Design.cast(app.activeProduct).appearances.itemByName(name)
        if color is None:
            return createColor(name, r, g, b)
        return color
    except RuntimeError:
        return createColor(name, r, g, b)


def createColor(name: str, r, g, b) -> Appearance:
    app = Application.get()
    futil.log(f"Creating new color: {name}")
    existingColor = app.materialLibraries[3].appearances.itemByName("Oak")
    newColor: Appearance = Design.cast(app.activeProduct).appearances.addByCopy(existingColor, name)
    colorProp = ColorProperty.cast(newColor.appearanceProperties.itemByName("Color"))
    colorProp.value = Color.create(r, g, b, 0)
    return newColor


def cutSketch(sketch: Sketch, targetOccurence: Occurrence, height: float):
    """
    Cuts a sketch with a specified height from a target occurrence.

    Args:
        sketch (Sketch): The sketch to be cut.
        targetOccurence (Occurrence): The target occurrence to cut the sketch from.
        height (float): The height of the cut.
    """
    profile = sketch.profiles.item(0)
    extrudes = targetOccurence.features.extrudeFeatures
    cutterInput = extrudes.createInput(profile, FeatureOperations.CutFeatureOperation)
    cutterInput.setDistanceExtent(False, ValueInput.createByReal(height))
    extrudes.add(cutterInput)


def exportStepFile(design: Design, export_path: str):
    exportManager = design.exportManager
    stepOptions = exportManager.createSTEPExportOptions(export_path, design.rootComponent)
    exportManager.execute(stepOptions)
