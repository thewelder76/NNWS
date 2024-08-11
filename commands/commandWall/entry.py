import os

import adsk.cam
from adsk.core import (
    BoolValueCommandInput,
    CommandCreatedEventArgs,
    CommandEventArgs,
    CommandInput,
    CommandInputs,
    GroupCommandInput,
    InputChangedEventArgs,
    IntegerSpinnerCommandInput,
    ObjectCollection,
    Point3D,
    StringValueCommandInput,
    TableCommandInput,
    ValueInput,
)
from adsk.fusion import Component, FeatureOperations, Occurrence, Sketch, SplitBodyFeature

from ... import config
from ...lib import fusion360utils as futil

# NNWS constants
from ...lib.common.nnws_constants import (
    CALLBACK_NAME,
    GRIDFINITY_SIZE_CM,
    NOTCH_SIZE_RADIUS_CM,
    THREAD_PITCH_CM,
    THREAD_SIZE_D_MAJOR_CM,
    WALL_BOTTOM_THICKNESS_CM,
    WALL_INNER_SECTION_OFFSET_CM,
    WALL_INNER_WALL_OFFSET_CM,
    WALL_OUTER_WALL_THICKNESS_CM,
    WALL_THICKNESS_CM,
)
from ...lib.common.nnws_util import *
from ...lib.common.wall_pattern import *

app = adsk.core.Application.get()
ui = app.userInterface

# UI Constants
MENU_WALL_FEATURE = "wall_features"
MENU_WALL_DROPDOWN = "wall_dropdown"

WALL = "Wall"

MENU_DIMENSION_GROUP = "dimension_group"
MENU_DIMENSION_PREVIEW = "dimension_preview"
MENU_DIMENSION_WIDTH = "dimension_width"
MENU_DIMENSION_HEIGHT = "dimension_height"
MENU_DIMENSION_STANDARD_WALL_PATTERN = "dimension_non_standard_wall_pattern"
WALL_NOTCH = "wall_notch"
WALL_PATTERN_TABLE = "wall_pattern_table"
WALL_PATTERN_RESET = "wall_pattern_reset"

# border options
MENU_BORDER_GENERATION_GROUP = "border_generation_group"
OPTION_TOP = "option_top"
OPTION_RIGHT = "option_right"
OPTION_BOTTOM = "option_bottom"
OPTION_LEFT = "option_left"

CMD_ID = f"{config.COMPANY_NAME}_{config.ADDIN_NAME}_cmdwall"
CMD_NAME = "NNWS Wall"
CMD_Description = "Create NNWS Wall."

# Specify that the command will be promoted to the panel.
IS_PROMOTED = True
WORKSPACE_ID = "FusionSolidEnvironment"
PANEL_ID = "SolidCreatePanel"
COMMAND_BESIDE_ID = ""

# Resource location for command icons, here we assume a sub folder in this directory named "resources".
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "")

# Local list of event handlers used to maintain a reference so
# they are not released and garbage collected.
local_handlers = []


# Executed when add-in is run.
def start():
    # Create a command Definition.
    cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)

    # Define an event handler for the command created event. It will be called when the button is clicked.
    futil.add_handler(cmd_def.commandCreated, command_created)

    # ******** Add a button into the UI so the user can run the command. ********
    # Get the target workspace the button will be created in.
    workspace = ui.workspaces.itemById(WORKSPACE_ID)

    # Get the panel the button will be created in.
    panel = workspace.toolbarPanels.itemById(PANEL_ID)

    # Create the button command control in the UI after the specified existing command.
    control = panel.controls.addCommand(cmd_def, COMMAND_BESIDE_ID, False)

    # Specify if the command is promoted to the main toolbar.
    control.isPromoted = IS_PROMOTED

    # this is the script handling code for stl automation generation
    cmdDef = ui.commandDefinitions.itemById(CALLBACK_NAME)
    if not cmdDef:
        cmdDef = ui.commandDefinitions.addButtonDefinition(CALLBACK_NAME, "Wall System Automation", "Automate Wall Creation")
        futil.add_handler(cmdDef.commandCreated, script_created)
        design = app.activeProduct
        userParams = design.userParameters
        userParams.add("script_exportPath", ValueInput.createByString("path"), "", "")


# Executed when add-in is stopped.
def stop():
    # Get the various UI elements for this command
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)

    script_definition = ui.commandDefinitions.itemById(CALLBACK_NAME)
    if script_definition:
        script_definition.deleteMe()
        design = app.activeProduct
        # deleting user's parameters created for the script automation
        design.userParameters.itemByName("script_exportPath").deleteMe()

    # Delete the button command control
    if command_control:
        command_control.deleteMe()

    # Delete the command definition
    if command_definition:
        command_definition.deleteMe()


def script_created(args: CommandCreatedEventArgs):
    futil.add_handler(args.command.execute, scriptGenerateWall, local_handlers=local_handlers)


# Function that is called when a user clicks the corresponding button in the UI.
# This defines the contents of the command dialog and connects to the command related events.
def command_created(args: CommandCreatedEventArgs):
    args.command.setDialogInitialSize(400, 600)
    inputs = args.command.commandInputs

    dimensionGroup = inputs.addGroupCommandInput(MENU_DIMENSION_GROUP, "Wall Dimensions")
    dimensionGroup.children.addBoolValueInput(MENU_DIMENSION_PREVIEW, "Preview", True, "", False)
    dimensionGroup.children.addIntegerSpinnerCommandInput(MENU_DIMENSION_WIDTH, "Wall X Count", 1, 99, 1, 2)
    heightInput = dimensionGroup.children.addIntegerSpinnerCommandInput(MENU_DIMENSION_HEIGHT, "Wall Y Count", 1, 99, 1, 2)
    dimensionGroup.children.addBoolValueInput(WALL_NOTCH, "Notch", True, "", True)
    equalSectionInput: BoolValueCommandInput = dimensionGroup.children.addBoolValueInput(MENU_DIMENSION_STANDARD_WALL_PATTERN, "Standard Wall Pattern", True, "", True)

    equalSectionInput.isEnabled = heightInput.value > 1

    buildTable(inputs, not equalSectionInput.isEnabled)

    # Future work for border generation
    # borderGroup = inputs.addGroupCommandInput(MENU_BORDER_GENERATION_GROUP, 'Border Generation')
    # borderGroup.children.addBoolValueInput(OPTION_TOP, 'Top border', True)
    # borderGroup.children.addBoolValueInput(OPTION_RIGHT, 'Right border', True)
    # borderGroup.children.addBoolValueInput(OPTION_BOTTOM, 'Bottom border', True)
    # borderGroup.children.addBoolValueInput(OPTION_LEFT, 'Left border', True)

    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.inputChanged, command_input_changed, local_handlers=local_handlers)
    futil.add_handler(args.command.executePreview, command_preview, local_handlers=local_handlers)
    # futil.add_handler(args.command.validateInputs, command_validate_input, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)


# This event handler is called when the user clicks the OK button in the command dialog or
# is immediately called after the created event not command inputs were created for the dialog.
def command_execute(args: CommandEventArgs):
    generateWall(args)


# This event handler is called when the command needs to compute a new preview in the graphics window.
def command_preview(args: CommandEventArgs):
    inputs = args.command.commandInputs
    preview = inputs.itemById(MENU_DIMENSION_GROUP).children.itemById(MENU_DIMENSION_PREVIEW)

    if preview and preview.value == True:
        generateWall(args)


# This event handler is called when the user changes anything in the command dialog
# allowing you to modify values of other inputs based on that change.
def command_input_changed(args: InputChangedEventArgs):
    if None == args.input.parentCommandInput:
        return

    # Button disabled for now, but keeping the condition for future use
    if args.input.id == WALL_PATTERN_RESET:
        futil.log("Resetting the wall pattern")
        # buildTable() ? # need to delete the table and recreate it?
    elif args.input.id == MENU_DIMENSION_HEIGHT:  # chaning the height, enable the options for the wall pattern
        heightInput: IntegerSpinnerCommandInput = args.inputs.itemById(MENU_DIMENSION_HEIGHT)
        widthInput: IntegerSpinnerCommandInput = args.inputs.itemById(MENU_DIMENSION_WIDTH)
        equalSectionInput: BoolValueCommandInput = args.inputs.itemById(MENU_DIMENSION_STANDARD_WALL_PATTERN)
        equalSectionInput.isEnabled = heightInput.value > 1

        table: TableCommandInput = args.input.parentCommandInput.commandInputs.itemById(WALL_PATTERN_TABLE)
        if table != None:
            handleDimensionChange(table, heightInput.value, widthInput.value, not equalSectionInput.value)
            table.isVisible = not equalSectionInput.value

            if heightInput.value == 1:
                table.isVisible = False
                equalSectionInput.value = True

    elif args.input.id == MENU_DIMENSION_STANDARD_WALL_PATTERN:  # if the non standard wall pattern is selected, disable the border options
        equalSectionInput: BoolValueCommandInput = args.input
        # Future work for border generation
        # borderInputs = args.input.parentCommandInput.commandInputs
        # if borderInputs != None:
        #     borderInputs.itemById(OPTION_TOP).isEnabled = equalSectionInput.value
        #     borderInputs.itemById(OPTION_RIGHT).isEnabled = equalSectionInput.value
        #     borderInputs.itemById(OPTION_BOTTOM).isEnabled = equalSectionInput.value
        #     borderInputs.itemById(OPTION_LEFT).isEnabled = equalSectionInput.value

        # if non standard wall pattern is selected, show the table
        table: TableCommandInput = args.input.parentCommandInput.commandInputs.itemById(WALL_PATTERN_TABLE)
        if table != None:
            heightInput: IntegerSpinnerCommandInput = args.inputs.itemById(MENU_DIMENSION_HEIGHT)
            widthInput: IntegerSpinnerCommandInput = args.inputs.itemById(MENU_DIMENSION_WIDTH)
            handleDimensionChange(table, heightInput.value, widthInput.value, not equalSectionInput.value)
            table.isVisible = not equalSectionInput.value


def handleDimensionChange(table: TableCommandInput, height, width, visible: bool):
    if table.rowCount - 1 < height:
        addRow(table, table.rowCount, width, 0, visible)
    elif table.rowCount - 1 > height:
        table.deleteRow(table.rowCount - 1)


# This event handler is called when the command terminates.
def command_destroy(args: CommandEventArgs):
    global local_handlers
    local_handlers = []


def buildTable(inputs: CommandInput, visible: bool):
    """
    Builds the table(spreadsheet) to specify the wall pattern

    Args:
        inputs (CommandInput): The input object.
        visible (bool): Indicates whether the table should be visible.

    Returns:
        None
    """
    dimensionGroup: GroupCommandInput = inputs.itemById(MENU_DIMENSION_GROUP)
    wallPatternTable: TableCommandInput = dimensionGroup.children.addTableCommandInput(WALL_PATTERN_TABLE, "Compartments", 3, "1:1:1")
    # Future
    # resetButton = dimensionGroup.commandInputs.addBoolValueInput(WALL_PATTERN_RESET, 'Reset', False, '', False)
    # resetButton.isVisible = visible
    # wallPatternTable.addToolbarCommandInput(resetButton)
    wallPatternTable.maximumVisibleRows = 20

    wallPatternTable.addCommandInput(buildTableTitleItem(wallPatternTable.commandInputs, "Row"), 0, 0)
    wallPatternTable.addCommandInput(buildTableTitleItem(wallPatternTable.commandInputs, "Count"), 0, 1)
    wallPatternTable.addCommandInput(buildTableTitleItem(wallPatternTable.commandInputs, "Offset"), 0, 2)

    heightInput = dimensionGroup.children.itemById(MENU_DIMENSION_HEIGHT)
    widthInput = dimensionGroup.children.itemById(MENU_DIMENSION_WIDTH)
    for row in range(heightInput.value):
        # row + 1 to account for the title row
        addRow(wallPatternTable, row + 1, widthInput.value, 0, visible)

    wallPatternTable.isVisible = visible


def buildTableTitleItem(commandInputs: CommandInputs, name: str) -> StringValueCommandInput:
    """
    Builds a table title item.

    Args:
        commandInputs (CommandInputs): The command inputs object.
        name (str): The name of the table title item.

    Returns:
        StringValueCommandInput: The table title item.
    """
    item = commandInputs.addStringValueInput(name, "", name)
    item.isReadOnly = True
    item.isFullWidth = True
    return item


def addRow(table: TableCommandInput, rowIndex: int, countValue: int, offsetValue: int, visible: bool):
    """
    Adds a row to the table with the specified inputs.

    Args:
        table (TableCommandInput): The table to add the row to.
        rowIndex (int): The index of the row.
        countValue (int): The initial value for the count input.
        offsetValue (int): The initial value for the offset input.
        visible (bool): Indicates whether the row should be visible.

    Returns:
        None
    """
    rowIndexInput = table.commandInputs.addStringValueInput("rowIndex", "", str(rowIndex))
    rowIndexInput.isReadOnly = True
    rowIndexInput.isVisible = visible
    countInput = table.commandInputs.addIntegerSpinnerCommandInput(f"count {rowIndex}", "Count", 1, 100, 1, countValue)
    countInput.isFullWidth = True
    countInput.isVisible = visible
    offsetInput = table.commandInputs.addIntegerSpinnerCommandInput(f"offset {rowIndex}", "Offset", -50, 50, 1, offsetValue)
    offsetInput.isFullWidth = True
    offsetInput.isVisible = visible
    # Disabling for now, to focus on the accessories
    # if rowIndex == 1:
    #     offsetInput.isEnabled = False
    offsetInput.isEnabled = False

    table.addCommandInput(rowIndexInput, rowIndex, 0)
    table.addCommandInput(countInput, rowIndex, 1)
    table.addCommandInput(offsetInput, rowIndex, 2)


def generateWall(args: CommandEventArgs):
    """
    This is the main function that will generate the wall based on the inputs from the user.
    This is creating a 1 wall unit and patterning it based on the user inputs.

    Args:
        args (CommandEventArgs): The command arguments.

    Returns:
        None
    """

    # Get the values from the inputs
    inputs = args.command.commandInputs
    dimensionGroup = inputs.itemById(MENU_DIMENSION_GROUP)
    widthInput = dimensionGroup.children.itemById(MENU_DIMENSION_WIDTH)
    heightInput = dimensionGroup.children.itemById(MENU_DIMENSION_HEIGHT)
    standardWallPattern: BoolValueCommandInput = dimensionGroup.children.itemById(MENU_DIMENSION_STANDARD_WALL_PATTERN)
    notch: BoolValueCommandInput = dimensionGroup.children.itemById(WALL_NOTCH)

    table: TableCommandInput = dimensionGroup.children.itemById(WALL_PATTERN_TABLE)

    # Border geneartion - Future work if needed
    # borderGeneartionGroup = inputs.itemById(MENU_BORDER_GENERATION_GROUP)
    # topBorder = borderGeneartionGroup.children.itemById(OPTION_TOP)
    # rightBorder = borderGeneartionGroup.children.itemById(OPTION_RIGHT)
    # bottomBorder = borderGeneartionGroup.children.itemById(OPTION_BOTTOM)
    # leftBorder = borderGeneartionGroup.children.itemById(OPTION_LEFT)

    internalGenerateWall(widthInput.value, heightInput.value, notch.value, standardWallPattern, table)


def scriptGenerateWall(exportPath: str):
    """Not used by the add-in; meant to be called by an external script."""

    futil.log("scriptGenerateWall: design wall system")

    for notch in [True, False]:
        for h in range(1, 9):
            for w in range(1, 9):
                design = internalGenerateWall(w, h, notch)
                filename = exportPath + f"{'/notched/' if notch else ''}wall_{w}x{h}{'_notched' if notch else ''}.step"
                futil.log(f"scriptGenerateWall: exporting to stl file '{filename}'")
                exportStepFile(design, filename)

                # clean up the design
                for c in design.rootComponent.allOccurrences:
                    c.deleteMe()


def internalGenerateWall(widthInput: int, heightInput: int, notch: bool, standardWallPattern: bool = True, table: TableCommandInput = None):
    design = app.activeProduct
    rootComponent: Component = Component.cast(design.rootComponent)

    # This is one section that will use to pattern the wall
    wallSection = createWallSection(rootComponent, notch)
    allBodyCollection = ObjectCollection.create()
    visibleBodyCollection = ObjectCollection.create()
    for body in wallSection.bRepBodies:
        allBodyCollection.add(body)
        if body.isVisible:
            visibleBodyCollection.add(body)

    xAxis = rootComponent.xConstructionAxis
    wallPatternDefinition = {}

    if table != None and standardWallPattern == False:
        for rowIndex in range(1, table.rowCount):  # skipping first row, it's the title
            wallPatternDefinition[rowIndex - 1] = [table.getInputAtPosition(rowIndex, 1).value, table.getInputAtPosition(rowIndex, 2).value]
    else:
        for i in range(heightInput):
            wallPatternDefinition[i] = [widthInput, 0]

    # first/top row and going down to be easier to match the table for non standard wall pattern
    patternBodies(rootComponent, xAxis, visibleBodyCollection, wallPatternDefinition[0][0])
    for rowIndex in wallPatternDefinition:
        if rowIndex > 0:
            width = wallPatternDefinition[rowIndex][0]
            offset = wallPatternDefinition[rowIndex][1]
            offset_angle = calculateOffsetAngle(WALL_NB_SIDES)
            r = GRIDFINITY_SIZE_CM / 2 / math.cos(math.pi / WALL_NB_SIDES)

            startPoint = createHexPoint(r, HexPointIndex.TOP.value, 0, offset_angle)
            toPoint = createHexPoint(r, HexPointIndex.BOTTOM_LEFT.value if rowIndex % 2 == 0 else HexPointIndex.BOTTOM_RIGHT.value, offset, offset_angle)
            delta = createDeltaVector(startPoint, toPoint)
            copyBodies(rootComponent, visibleBodyCollection, delta)
            patternBodies(rootComponent, xAxis, visibleBodyCollection, width)

    return design


def createWallSection(rootComponent: Component, notch: bool) -> Occurrence:
    """
    Create a wall section that will be patterned to create the wall

    Args:
        rootComponent (Component): The root component to create the wall section in.
        notch (bool): Indicates whether to create a notch in the wall section.

    Returns:
        Occurrence: The created wall section component.
    """
    wallComponent = createNamedComponent(rootComponent, WALL)

    # Wall Body
    outerRadius = GRIDFINITY_SIZE_CM / 2
    createExteriorWallSection(wallComponent.component, outerRadius, WALL_OUTER_WALL_THICKNESS_CM, WALL_THICKNESS_CM)
    outerRadius = GRIDFINITY_SIZE_CM / 2 - WALL_OUTER_WALL_THICKNESS_CM
    createHollowCylinder(wallComponent.component, outerRadius, WALL_INNER_WALL_OFFSET_CM, WALL_BOTTOM_THICKNESS_CM)
    outerRadius = GRIDFINITY_SIZE_CM / 2 - WALL_OUTER_WALL_THICKNESS_CM - WALL_INNER_WALL_OFFSET_CM
    internalSectionHeight = WALL_THICKNESS_CM - WALL_INNER_SECTION_OFFSET_CM
    mainWallBodyPart3: ExtrudeFeatures = createHollowCylinder(wallComponent.component, outerRadius, WALL_INNER_WALL_OFFSET_CM, internalSectionHeight)

    # Create the Inner Chamfer
    # the chamfer start at 1 mm from the bottom, so we need to calculate the height of the chamfer based on the internal section height and based on the angle of the chamfer
    createAnchorChamfer(wallComponent, mainWallBodyPart3.faces.item(0).edges.item(0), internalSectionHeight - 0.1)

    if notch:
        createNotch(wallComponent.component, outerRadius, internalSectionHeight, FeatureOperations.CutFeatureOperation)

    threadStartOffset = WALL_BOTTOM_THICKNESS_CM + THREAD_PITCH_CM
    internalThread = createInternalThread(
        wallComponent.component,
        threadStartOffset,  # threadStartOffset
        THREAD_SIZE_D_MAJOR_CM / 2,  # radius
        WALL_THICKNESS_CM,  # height
    )

    facesForFillet = None
    for b in wallComponent.component.bRepBodies:
        for f in b.faces:
            if math.isclose(f.pointOnFace.z, WALL_THICKNESS_CM, abs_tol=0.01):
                facesForFillet = f

    # Create SplitBodyFeatureInput
    splitBodyFeature: SplitBodyFeature = rootComponent.features.splitBodyFeatures
    splitBodyInput = splitBodyFeature.createInput(internalThread.bodies.item(0), facesForFillet, True)

    # Create split body feature
    splitedBodies = splitBodyFeature.add(splitBodyInput)
    for s in splitedBodies.bodies:
        if s.name == "Body4":
            # just hides the body
            s.isVisible = False

    filletEdges(rootComponent, wrapInCollection(facesForFillet.edges.item(0)), 0.05)

    return wallComponent


def createExteriorWallSection(targetOccurence: Occurrence, outerRadius: float, offset: float, height: float) -> Sketch:
    """
    Creates an exterior wall section that will connect to each other.

    Args:
        targetOccurence (Occurrence): The target occurrence where the wall section will be created.
        outerRadius (float): The outer radius of the wall section.
        offset (float): The offset from the outer circle to the inner circle.
        height (float): The height of the wall section.

    Returns:
        Sketch: The outer sketch of the wall section.
    """

    sketches = targetOccurence.sketches
    xy_plane = targetOccurence.xYConstructionPlane
    outer_sketch = sketches.add(xy_plane)
    outer_sketch.name = "Outer Sketch"
    createExteriorContainer(outer_sketch, outerRadius)

    # Create a second sketch for the inner circle
    inner_sketch = sketches.add(xy_plane)
    inner_circle = inner_sketch.sketchCurves.sketchCircles.addByCenterRadius(Point3D.create(0, 0, 0), outerRadius - offset)

    # Create a profile from the outer circle
    outer_profile = outer_sketch.profiles.item(0)

    # Create an extrusion for the cylinder
    extrudes = targetOccurence.features.extrudeFeatures
    extrude_input = extrudes.createInput(outer_profile, FeatureOperations.NewBodyFeatureOperation)
    extrude_distance = ValueInput.createByReal(height)
    extrude_input.setDistanceExtent(False, extrude_distance)
    cylinder = extrudes.add(extrude_input)

    # Create a profile from the inner circle
    inner_profile = inner_sketch.profiles.item(0)

    # Create a second extrusion to remove material and create the hole
    hole_extrude_input = extrudes.createInput(inner_profile, FeatureOperations.CutFeatureOperation)
    hole_extrude_input.setDistanceExtent(False, extrude_distance)
    extrudes.add(hole_extrude_input)

    return outer_sketch


def createExteriorContainer(sketch: Sketch, radius: float):
    """
    Create a hexagon shape for the outer wall or a wall section

    Args:
        sketch (Sketch): The sketch object to draw the lines on.
        radius (float): The radius of the container.

    Returns:
        None
    """

    points = ObjectCollection.create()
    nbSides = WALL_NB_SIDES
    r = radius / math.cos(math.pi / nbSides)

    # Ensure the first point starts at the top of the circle for vertical sides
    offset_angle = calculateOffsetAngle(nbSides)
    for i in range(nbSides):
        points.add(createHexPoint(r, i, 0, offset_angle))

    # Connect the points with lines to form the polygon
    for i in range(nbSides):
        start_point = points.item(i)
        end_point = points.item((i + 1) % nbSides)
        sketch.sketchCurves.sketchLines.addByTwoPoints(start_point, end_point)


def createNotch(targetOccurence: Occurrence, outerRadius: float, height: float, operationType: FeatureOperations):
    """
    Notch the wall accessories backing so they are angled at predefined angle

    Parameters:
    - targetOccurence (Occurrence): The target occurrence on which the notch will be created.
    - outerRadius (float): The outer radius of the notch.
    - height (float): The height of the notch.
    - operationType (FeatureOperations): The type of operation to be performed on the notch.

    Returns:
        None
    """
    sketches = targetOccurence.sketches
    xz_plane = targetOccurence.xZConstructionPlane

    sketch = sketches.add(xz_plane)
    sketch.name = "Notch"
    sketch.sketchCurves.sketchCircles.addByCenterRadius(Point3D.create(0, -height - NOTCH_SIZE_RADIUS_CM / 2, 0), NOTCH_SIZE_RADIUS_CM)
    circPatternSketch(targetOccurence, operationType, sketch, outerRadius, 8, targetOccurence.zConstructionAxis)
