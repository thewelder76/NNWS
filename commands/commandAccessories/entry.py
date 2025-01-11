import math
import os
import traceback

from adsk.core import (
    Application,
    CommandCreatedEventArgs,
    CommandEventArgs,
    DropDownCommandInput,
    DropDownStyles,
    GroupCommandInput,
    HorizontalAlignments,
    InputChangedEventArgs,
    ObjectCollection,
    Point3D,
    ValidateInputsEventArgs,
    ValueInput,
)
from adsk.fusion import (
    BRepFace,
    CircularPatternFeature,
    CombineFeatureInput,
    Component,
    ConstructionPlaneInput,
    ExtrudeFeature,
    FeatureOperations,
    HoleFeature,
    HoleFeatures,
    LoftFeature,
    Occurrence,
    PatternDistanceType,
    RectangularPatternFeatures,
    Sketch,
    SketchLine,
    SketchLineList,
    SweepFeature,
    TextStyles,
)

from ... import config
from ...commands.commandAccessories.screw_definitions import (
    ScrewDefinitionsEnum,
)
from ...lib import fusion360utils as futil

# NNWS constants
from ...lib.common.nnws_constants import (
    ACC_ANCHOR_TOP_OFFSET_CM,
    ACC_EXTENSION_HEIGTH_CM,
    ACC_EXTENSION_WIDTH_CM,
    ACC_EXTRA_SPACING_DEFAULT_CM,
    ACC_INTERNAL_SKETCH_RADIUS_CM,
    ACC_LEDGER_WIDTH_CM,
    ACC_SHELF_WIDTH_CM,
    EXTERNAL_TOLERANCE_CM,
    GRIDFINITY_BASE_HEIGHT_CM,
    GRIDFINITY_BASE_HEIGHT_MM,
    GRIDFINITY_SIZE_CM,
    GRIDFINITY_Z_OFFSET_CM,
    H_NEW_CM,
    HEAD_OFFSET_CM,
    INTERNAL_WALL_CHAMFER_ANGLE,
    MAIN_SCREW_BODY_CLEARANCE_CM,
    MAIN_SCREW_BODY_CLEARANCE_MM,
    MAIN_SCREW_BODY_END_CLEARANCE_CM,
    MAIN_SCREW_HEAD_INTERNAL_DIAMETER_CM,
    MAIN_SCREW_HEAD_THICKNESS_CM,
    MAIN_SCREW_HEIGHT_CM,
    MAIN_SCREW_THREAD_BODY_THICKNESS_CM,
    MIN_SHELF_SIZE_CM,
    MIN_SHELF_SIZE_MM,
    MIN_SHELF_THICKNESS_CM,
    NOTCH_SIZE_RADIUS_CM,
    THREAD_SIZE_D_MAJOR_CM,
    UNIT_DEG,
    UNIT_MM,
    WALL_INNER_SECTION_OFFSET_CM,
    WALL_INNER_WALL_OFFSET_CM,
    WALL_OUTER_WALL_THICKNESS_CM,
    WALL_THICKNESS_CM,
)
from ...lib.common.nnws_util import (
    calculateChamferWidth,
    create2PointRectFromPoints,
    createAnchorChamfer,
    createCylinder,
    createCylinderFromPoint,
    createCylinderFromPointXYPlane,
    createCylinderFromPointXZPlane,
    createExternalThread,
    createNamedComponent,
    createOffsetPlane,
    createPolygon,
    filletEdges,
    selectFaceAt,
    selectTopFace,
    valueInputMinMax,
    wrapInCollection,
)
from ...lib.common.wall_pattern import (
    WALL_NB_SIDES,
    HexPointIndex,
    calculateOffsetAngle,
    circPatternSketch,
    copyBodies,
    createDeltaVector,
    patternBodies,
)

# TODO list
# Add user parameters to the model with all the used values that can be changed and re-used.

app = Application.get()
ui = app.userInterface

# clearance input as global variable to easily access the input for calculations
global clearanceInput

# UI Constants
MENU_ACC_GENERAL_SETTINGS = "acc_general_settings"
MENU_ACC_FEATURE = "acc_features"
MENU_ACC_DROPDOWN = "acc_dropdown"

MENU_GENERAL_PREVIEW = "general_preview"

# Clearance menu
CLEARANCE_MENU_ID = "clearance_menu_id"
CLEARANCE_MENU_INPUT = "clearance_menu_input"

# Accessories Drop Down Options
MENU_MAIN_SCREW = "Main Screw"
MENU_INSERT = "Base Insert"
MENU_SHELF = "Shelf Support"
MENU_SHELF_INSERT = "Shelf Insert"
MENU_HOOK = "Hook"
MENU_ANCHOR = "Fastening Anchor"
MENU_OFFSET_ANCHOR = "Offset Fastening Anchor Set"

# Main Screw Options
MENU_MAIN_SCREW_GROUP = "main_screw_group"
MAIN_SCREW_HEIGHT = "main_screw_height"

# Base insert menu
MENU_INSERT_GROUP = "insert_group"
MENU_INSERT_TRIM_TOP = "insert_trim_top"
MENU_INSERT_TRIM_BOTTOM_TEXT = "insert_trim_bottom_text"
MENU_INSERT_TRIM_BOTTOM = "insert_trim_bottom"
MENU_INSERT_EXTRA_SPACING = "insert_extra_spacing"
MENU_INSERT_NOTCH = "insert_notch"
MENU_INSERT_INVERSE = "insert_inverse"
MENU_INSERT_X_COUNT = "insert_x_count"
MENU_INSERT_Y_COUNT = "insert_y_count"

# Shelf options
MENU_SHELF_GROUP = "shelf_group"
MENU_SHELF_TRIM_TOP = "shelf_trim_top"
MENU_SHELF_TRIM_BOTTOM = "shelf_trim_bottom"
MENU_SHELF_EXTRA_SPACING = "shelf_extra_spacing"
MENU_SHELF_NOTCH = "shelf_notch"
MENU_SHELF_X_COUNT = "shelf_x_count"
MENU_SHELF_DEPTH = "shelf_depth"
MENU_SHELF_LENGTH = "shelf_length"
MENU_SHELF_INVERSE = "shelf_inverse"
MENU_SHELF_ERROR = "shelf_error"
MENU_SHELF_GRIDFINITY_GEN_INSTALLED = "shelf_gridfinity_gen_installed"

MENU_SHELF_INSERT_GROUP = "shelf_insert_group"
MENU_SHELF_INSERT_NOTCH = "shelf_insert_notch"
MENU_SHELF_INSERT_THICKNESS = "shelf_insert_thickness"
MENU_SHELF_INSERT_DEPTH = "shelf_insert_depth"
MENU_SHELF_INSERT_LENGTH = "shelf_insert_length"

MENU_HOOK_GROUP = "hook_group"
MENU_HOOK_NOTCH = "hook_notch"
MENU_HOOK_SIZE = "hook_size"
MENU_HOOK_TRIM_TOP = "hook_trim_top"
MENU_HOOK_TRIM_BOTTOM = "hook_trim_bottom"
MENU_HOOK_LENGTH = "hook_height"
MENU_HOOK_STOPPER = "hook_stopper"
MENU_HOOK_STOPPER_HEIGHT = "hook_stopper_height"

MENU_ANCHOR_GROUP = "anchor_group"
MENU_ANCHOR_TOP_OFFSET = "anchor_top_offset"
MENU_ANCHOR_SCREWTYPE = "anchor_screwtype"
MENU_ANCHOR_HEAD_DIAMETER = "anchor_head_diameter"
MENU_ANCHOR_COUNTERSINK_ANGLE = "anchor_countersink_angle"
MENU_ANCHOR_HOLE_DIAMETER = "anchor_hole_diameter"
MENU_ANCHOR_SCREWTYPE_CUSTOM = "Custom"

CMD_ID = f"{config.COMPANY_NAME}_{config.ADDIN_NAME}_cmdAccessories"
CMD_NAME = "NNWS Accessories"
CMD_Description = "Create NNWS Accessories."

# Specify that the command will be promoted to the panel.
IS_PROMOTED = True
WORKSPACE_ID = "FusionSolidEnvironment"
# PANEL_ID = "SolidCreatePanel"
# COMMAND_BESIDE_ID = ""
PANEL_ID = 'SolidScriptsAddinsPanel' # for easy testing...
COMMAND_BESIDE_ID = 'ScriptsManagerCommand'

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


# Executed when add-in is stopped.
def stop():
    # Get the various UI elements for this command

    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)

    # Delete the button command control
    if command_control:
        command_control.deleteMe()

    # Delete the command definition
    if command_definition:
        command_definition.deleteMe()


# Function that is called when a user clicks the corresponding button in the UI.
# This defines the contents of the command dialog and connects to the command related events.
def command_created(args: CommandCreatedEventArgs):
    args.command.setDialogInitialSize(400, 600)

    inputs = args.command.commandInputs
    generalGroup = inputs.addGroupCommandInput(MENU_ACC_GENERAL_SETTINGS, "General Settings")
    generalGroup.children.addBoolValueInput(MENU_GENERAL_PREVIEW, "Preview", True, "", True)
    generalGroup.children.addTextBoxCommandInput(
        CLEARANCE_MENU_ID, "", "The clearance setting applies to all accessories.\nDefault is " + str(MAIN_SCREW_BODY_CLEARANCE_MM) + " mm", 2, True
    )
    global clearanceInput
    clearanceInput = valueInputMinMax(generalGroup, CLEARANCE_MENU_INPUT, "Clearance", UNIT_MM, MAIN_SCREW_BODY_CLEARANCE_CM, 0, 0.025)

    # to easily switch between the different accessories for testing as they are the main development focus
    # insertDefaultVisibility = True
    insertDefaultVisibility = False
    accTypeDropdown = generalGroup.children.addDropDownCommandInput(MENU_ACC_DROPDOWN, "Accessorie type", DropDownStyles.LabeledIconDropDownStyle)
    accTypeDropdown.listItems.add(MENU_MAIN_SCREW, False)
    accTypeDropdown.listItems.add(MENU_INSERT, insertDefaultVisibility)
    accTypeDropdown.listItems.add(MENU_SHELF, not insertDefaultVisibility)
    accTypeDropdown.listItems.add(MENU_SHELF_INSERT, False)
    # accTypeDropdown.listItems.add(MENU_HOOK, False)
    accTypeDropdown.listItems.add(MENU_HOOK, True)
    accTypeDropdown.listItems.add(MENU_ANCHOR, False)
    accTypeDropdown.listItems.add(MENU_OFFSET_ANCHOR, False)

    mainScrewGroup: GroupCommandInput = inputs.addGroupCommandInput(MENU_MAIN_SCREW_GROUP, "Main Screw Option")
    valueInputMinMax(
        mainScrewGroup,
        MAIN_SCREW_HEIGHT,
        "Height ( Effective Height from bottom of head )",
        UNIT_MM,
        MAIN_SCREW_HEIGHT_CM - MAIN_SCREW_BODY_END_CLEARANCE_CM,
        MAIN_SCREW_HEIGHT_CM - MAIN_SCREW_BODY_END_CLEARANCE_CM,
    )
    mainScrewGroup.isVisible = False

    # Insert Group
    insertGroup: GroupCommandInput = inputs.addGroupCommandInput(MENU_INSERT_GROUP, "Base Insert Option")
    valueInputMinMax(insertGroup, MENU_INSERT_TRIM_TOP, "Top/Right Width (Trim)", UNIT_MM, getScrewInnerRadius(), 0)
    trimMsg = (
        "The Bottom/Left Trim defaults to the gridfinity based height ("
        + str(GRIDFINITY_BASE_HEIGHT_MM)
        + " mm) / 2. This allow the bottom to be flushed with the based and easily print."
    )
    insertGroup.children.addTextBoxCommandInput(MENU_INSERT_TRIM_BOTTOM_TEXT, "", trimMsg, 3, True)
    valueInputMinMax(insertGroup, MENU_INSERT_TRIM_BOTTOM, "Bottom/Left Width (Trim)", UNIT_MM, GRIDFINITY_BASE_HEIGHT_CM / 2, 0)
    valueInputMinMax(insertGroup, MENU_INSERT_EXTRA_SPACING, "Extra Spacing", UNIT_MM, ACC_EXTRA_SPACING_DEFAULT_CM, 0)
    insertGroup.children.addBoolValueInput(MENU_INSERT_NOTCH, "Notch", True, "", True)
    # TODO not sure that this is as useful as I thought it would be
    insertGroup.children.addBoolValueInput(MENU_INSERT_INVERSE, "Invert the Trim direction", True, "", True)
    insertGroup.children.addIntegerSpinnerCommandInput(MENU_INSERT_X_COUNT, "Insert X Count", 1, 5, 1, 1)
    insertGroup.children.addIntegerSpinnerCommandInput(MENU_INSERT_Y_COUNT, "Insert Y Count", 1, 5, 1, 1)
    insertGroup.isVisible = insertDefaultVisibility

    insertDepthMsg = "Shelf Depth. min " + str(MIN_SHELF_SIZE_MM) + " mm"
    insertLengthMsg = "Shelf Length. min " + str(MIN_SHELF_SIZE_MM) + " mm"

    # Shelf Group
    shelfGroup: GroupCommandInput = inputs.addGroupCommandInput(MENU_SHELF_GROUP, "Shelf Option")
    valueInputMinMax(shelfGroup, MENU_SHELF_TRIM_TOP, "Top/Right Width (Trim)", UNIT_MM, getScrewInnerRadius(), 0)
    valueInputMinMax(shelfGroup, MENU_SHELF_TRIM_BOTTOM, "Bottom/Left Width (Trim)", UNIT_MM, ACC_EXTENSION_HEIGTH_CM / 2, 0)
    valueInputMinMax(shelfGroup, MENU_SHELF_EXTRA_SPACING, "Extra Spacing", UNIT_MM, ACC_EXTRA_SPACING_DEFAULT_CM, 0)
    shelfGroup.children.addBoolValueInput(MENU_SHELF_NOTCH, "Notch", True, "", True)
    shelfGroup.children.addBoolValueInput(MENU_SHELF_INVERSE, "Invert the Trim direction", True, "", True)
    xCount = shelfGroup.children.addIntegerSpinnerCommandInput(MENU_SHELF_X_COUNT, "Insert X Count", 1, 5, 1, 2)
    valueInputMinMax(shelfGroup, MENU_SHELF_DEPTH, insertDepthMsg, UNIT_MM, 2 * GRIDFINITY_SIZE_CM, MIN_SHELF_SIZE_CM)
    valueInputMinMax(shelfGroup, MENU_SHELF_LENGTH, insertLengthMsg, UNIT_MM, xCount.value * GRIDFINITY_SIZE_CM, MIN_SHELF_SIZE_CM)
    shelfGroup.children.addTextBoxCommandInput(MENU_SHELF_ERROR, "", "", 2, True)
    # shelfGroup.isVisible = not insertDefaultVisibility
    shelfGroup.isVisible = False

    # Shelf Insert Group
    shelfInsertGroup: GroupCommandInput = inputs.addGroupCommandInput(MENU_SHELF_INSERT_GROUP, "Shelf Insert Option")
    shelfInsertGroup.children.addBoolValueInput(MENU_SHELF_INSERT_NOTCH, "Notch", True, "", True)
    insertThicknessMsg = "Shelf Thickness, min " + str(MIN_SHELF_THICKNESS_CM) + " mm"
    valueInputMinMax(shelfInsertGroup, MENU_SHELF_INSERT_THICKNESS, insertThicknessMsg, UNIT_MM, MIN_SHELF_THICKNESS_CM, MIN_SHELF_THICKNESS_CM)
    valueInputMinMax(shelfInsertGroup, MENU_SHELF_INSERT_DEPTH, insertDepthMsg, UNIT_MM, 2 * (GRIDFINITY_SIZE_CM - ACC_LEDGER_WIDTH_CM), MIN_SHELF_SIZE_CM)
    valueInputMinMax(shelfInsertGroup, MENU_SHELF_INSERT_LENGTH, insertLengthMsg, UNIT_MM, xCount.value * (GRIDFINITY_SIZE_CM - ACC_LEDGER_WIDTH_CM), MIN_SHELF_SIZE_CM)
    shelfInsertGroup.isVisible = False

    # Hook group
    hookGroup: GroupCommandInput = inputs.addGroupCommandInput(MENU_HOOK_GROUP, "Hook Option")
    hookGroup.children.addBoolValueInput(MENU_HOOK_NOTCH, "Notch", True, "", True)
    valueInputMinMax(hookGroup, MENU_HOOK_TRIM_TOP, "Top/Right Width (Trim)", UNIT_MM, getScrewInnerRadius(), 0)
    valueInputMinMax(hookGroup, MENU_HOOK_TRIM_BOTTOM, "Bottom/Left Width (Trim)", UNIT_MM, ACC_EXTENSION_HEIGTH_CM / 2, 0)
    valueInputMinMax(hookGroup, MENU_HOOK_SIZE, "Size ( always start from the bottom)", UNIT_MM, ACC_EXTENSION_HEIGTH_CM, 0.75)
    valueInputMinMax(hookGroup, MENU_HOOK_LENGTH, "Hook Length (From the base of the insert)", UNIT_MM, 7.5, 0)
    hookGroup.children.addBoolValueInput(MENU_HOOK_STOPPER, "Stopper", True, "", True)
    valueInputMinMax(hookGroup, MENU_HOOK_STOPPER_HEIGHT, "Stopper Height", UNIT_MM, 0.5, 0)

    # Anchor Group
    anchorGroup: GroupCommandInput = inputs.addGroupCommandInput(MENU_ANCHOR_GROUP, "Anchor Option")
    # for predefined screw selection
    valueInputMinMax(
        anchorGroup,
        MENU_ANCHOR_TOP_OFFSET,
        "Clearance from Top of the anchor",
        UNIT_MM,
        ACC_ANCHOR_TOP_OFFSET_CM,
        0,
        WALL_THICKNESS_CM - WALL_INNER_SECTION_OFFSET_CM - ACC_ANCHOR_TOP_OFFSET_CM,
    )
    anchorGroup.children.addDropDownCommandInput(MENU_ANCHOR_SCREWTYPE, "Screw/Bolt type", DropDownStyles.LabeledIconDropDownStyle)
    defaultSelectedScrew = ScrewDefinitionsEnum.M5
    for screwType in ScrewDefinitionsEnum.list():
        anchorGroup.children.itemById(MENU_ANCHOR_SCREWTYPE).listItems.add(screwType.displayName, screwType.displayName == defaultSelectedScrew.value.displayName)
    anchorGroup.children.itemById(MENU_ANCHOR_SCREWTYPE).listItems.add(MENU_ANCHOR_SCREWTYPE_CUSTOM, False)
    # display the hole size for the selected screw and let custom selection
    valueInputMinMax(anchorGroup, MENU_ANCHOR_HEAD_DIAMETER, "Head Diameter", UNIT_MM, defaultSelectedScrew.value.headDiameter, MAIN_SCREW_BODY_CLEARANCE_CM)
    valueInputMinMax(anchorGroup, MENU_ANCHOR_COUNTERSINK_ANGLE, "Countersink Angle", UNIT_DEG, defaultSelectedScrew.value.countersinkAngle, 1, 179)
    valueInputMinMax(anchorGroup, MENU_ANCHOR_HOLE_DIAMETER, "Hole Diameter", UNIT_MM, defaultSelectedScrew.value.holeDiameter, MAIN_SCREW_BODY_CLEARANCE_CM, 10)
    anchorGroup.isVisible = False

    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.inputChanged, command_input_changed, local_handlers=local_handlers)
    futil.add_handler(args.command.executePreview, command_preview, local_handlers=local_handlers)
    futil.add_handler(args.command.validateInputs, command_validate_input, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)


def updateScrewDefinitionValues():
    pass


def select(selected: DropDownCommandInput, args: CommandEventArgs):
    """
    Calls the proper part geneartion base on selection for generation and preview
    """

    if MENU_MAIN_SCREW == selected:
        generateMainScrew(args)
    elif MENU_INSERT == selected:
        generateInsert(args)
    elif MENU_SHELF == selected:
        generateShelf(args)
    elif MENU_SHELF_INSERT == selected:
        generateShelfInsert(args)
    elif MENU_HOOK == selected:
        generateHook(args)
    elif MENU_ANCHOR == selected:
        generateAnchor(args)
    elif MENU_OFFSET_ANCHOR == selected:
        generateAnchor(args, True)


# This event handler is called when the user clicks the OK button in the command dialog or
# is immediately called after the created event not command inputs were created for the dialog.
def command_execute(args: CommandEventArgs):
    try:
        inputs = args.command.commandInputs
        selected: DropDownCommandInput = inputs.itemById(MENU_ACC_DROPDOWN).selectedItem.name
        select(selected, args)
    except RuntimeError:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))


# This event handler is called when the user changes anything in the command dialog
# allowing you to modify values of other inputs based on that change.
def command_input_changed(args: InputChangedEventArgs):
    typeSelection = None
    if args and isinstance(args.input, DropDownCommandInput):  # TODO classType would probably work here
        if args.input.id == MENU_ACC_DROPDOWN:
            typeSelection = args.input.selectedItem.name
        if args.input.id == MENU_ANCHOR_SCREWTYPE and args.input.selectedItem.name != MENU_ANCHOR_SCREWTYPE_CUSTOM:
            screwDefinition = ScrewDefinitionsEnum.byName(args.input.selectedItem.name)
            args.input.parentCommandInput.commandInputs.itemById(MENU_ANCHOR_HEAD_DIAMETER).value = screwDefinition.headDiameter
            args.input.parentCommandInput.commandInputs.itemById(MENU_ANCHOR_COUNTERSINK_ANGLE).value = math.radians(screwDefinition.countersinkAngle)
            args.input.parentCommandInput.commandInputs.itemById(MENU_ANCHOR_HOLE_DIAMETER).value = screwDefinition.holeDiameter

    # 2 steps implementation, first hide all the groups and then show the selected one
    # this is also called when a value input is changed, so we need to check if the selected is not None
    if typeSelection is not None:
        for group in [MENU_MAIN_SCREW_GROUP, MENU_INSERT_GROUP, MENU_SHELF_GROUP, MENU_SHELF_INSERT_GROUP, MENU_HOOK_GROUP, MENU_ANCHOR_GROUP]:
            args.input.parentCommandInput.commandInputs.itemById(group).isVisible = False

    # enable the group for the selected option
    # Future, was trying ideas with screw height, but not pursuing it for now. Leaving the code here for future reference
    # Still using the value from the input selection though
    # if MENU_MAIN_SCREW == typeSelection:
    #     args.input.parentCommandInput.commandInputs.itemById(MENU_MAIN_SCREW_GROUP).isVisible = True

    if MENU_INSERT == typeSelection:
        args.input.parentCommandInput.commandInputs.itemById(MENU_INSERT_GROUP).isVisible = True

    if MENU_SHELF == typeSelection:
        args.input.parentCommandInput.commandInputs.itemById(MENU_SHELF_GROUP).isVisible = True

    if MENU_SHELF_INSERT == typeSelection:
        args.input.parentCommandInput.commandInputs.itemById(MENU_SHELF_INSERT_GROUP).isVisible = True
    
    if MENU_HOOK == typeSelection:
        args.input.parentCommandInput.commandInputs.itemById(MENU_HOOK_GROUP).isVisible = True

    if MENU_SHELF_X_COUNT == args.input.id:
        xCount = args.input.parentCommandInput.commandInputs.itemById(MENU_SHELF_X_COUNT).value
        args.input.parentCommandInput.commandInputs.itemById(MENU_SHELF_LENGTH).value = xCount * GRIDFINITY_SIZE_CM

    if MENU_ANCHOR == typeSelection or MENU_OFFSET_ANCHOR == typeSelection:
        args.input.parentCommandInput.commandInputs.itemById(MENU_ANCHOR_GROUP).isVisible = True

    # select the Custom option when the user any of the screw inputs
    if MENU_ANCHOR_HEAD_DIAMETER == args.input.id or MENU_ANCHOR_COUNTERSINK_ANGLE == args.input.id or MENU_ANCHOR_HOLE_DIAMETER == args.input.id:
        args.input.parentCommandInput.commandInputs.itemById(MENU_ANCHOR_SCREWTYPE).listItems[-1].isSelected = True


def command_preview(args: CommandEventArgs):
    try:
        inputs = args.command.commandInputs
        preview = inputs.itemById(MENU_ACC_GENERAL_SETTINGS).children.itemById(MENU_GENERAL_PREVIEW)

        if preview and preview.value:
            selected: DropDownCommandInput = inputs.itemById(MENU_ACC_DROPDOWN).selectedItem.name
            select(selected, args)
    except RuntimeError:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))


# This event handler is called when the user interacts with any of the inputs in the dialog
# which allows you to verify that all of the inputs are valid and enables the OK button.
def command_validate_input(args: ValidateInputsEventArgs):
    inputs = args.inputs

    args.areInputsValid = clearanceInput.value >= 0 and clearanceInput.value <= 0.025
    if not args.areInputsValid:
        return

    if inputs.itemById(MENU_INSERT_GROUP).isVisible:
        topTrim = inputs.itemById(MENU_INSERT_GROUP).children.itemById(MENU_INSERT_TRIM_TOP).value
        bottomTrim = inputs.itemById(MENU_INSERT_GROUP).children.itemById(MENU_INSERT_TRIM_BOTTOM).value
        extraSpacing = inputs.itemById(MENU_INSERT_GROUP).children.itemById(MENU_INSERT_EXTRA_SPACING).value
        args.areInputsValid = topTrim > 0 and bottomTrim > 0 and extraSpacing >= 0

    if inputs.itemById(MENU_SHELF_GROUP).isVisible:
        topTrim = inputs.itemById(MENU_SHELF_GROUP).children.itemById(MENU_SHELF_TRIM_TOP).value
        bottomTrim = inputs.itemById(MENU_SHELF_GROUP).children.itemById(MENU_SHELF_TRIM_BOTTOM).value
        extraSpacing = inputs.itemById(MENU_SHELF_GROUP).children.itemById(MENU_SHELF_EXTRA_SPACING).value
        shelfDepth = inputs.itemById(MENU_SHELF_GROUP).children.itemById(MENU_SHELF_DEPTH).value
        shelfLength = inputs.itemById(MENU_SHELF_GROUP).children.itemById(MENU_SHELF_LENGTH).value

        #  checking if it's too tight with the number of inserts
        xCount = inputs.itemById(MENU_SHELF_GROUP).children.itemById(MENU_SHELF_X_COUNT).value
        numFits = int(shelfLength // GRIDFINITY_SIZE_CM)
        sideWidth = (shelfLength - max(xCount - 1, numFits - 1) * GRIDFINITY_SIZE_CM) / 2
        if sideWidth < 0.75:
            inputs.itemById(MENU_SHELF_GROUP).children.itemById(MENU_SHELF_ERROR).text = "The shelf is too small for the number of inserts, could not calculate fillet."
        else:  # clear the error
            inputs.itemById(MENU_SHELF_GROUP).children.itemById(MENU_SHELF_ERROR).text = ""

        args.areInputsValid = topTrim > 0 and bottomTrim > 0 and extraSpacing >= 0 and shelfDepth >= MIN_SHELF_SIZE_CM and shelfLength >= MIN_SHELF_SIZE_CM

    if inputs.itemById(MENU_SHELF_INSERT_GROUP).isVisible:
        shelfThickness = inputs.itemById(MENU_SHELF_INSERT_GROUP).children.itemById(MENU_SHELF_INSERT_THICKNESS).value
        shelfDepth = inputs.itemById(MENU_SHELF_INSERT_GROUP).children.itemById(MENU_SHELF_INSERT_DEPTH).value
        shelfLength = inputs.itemById(MENU_SHELF_INSERT_GROUP).children.itemById(MENU_SHELF_INSERT_LENGTH).value
        args.areInputsValid = shelfThickness >= MIN_SHELF_THICKNESS_CM and shelfDepth >= MIN_SHELF_SIZE_CM and shelfLength >= MIN_SHELF_SIZE_CM

    if inputs.itemById(MENU_HOOK_GROUP).isVisible:
        topTrim = inputs.itemById(MENU_HOOK_GROUP).children.itemById(MENU_HOOK_TRIM_TOP).value
        bottomTrim = inputs.itemById(MENU_HOOK_GROUP).children.itemById(MENU_HOOK_TRIM_BOTTOM).value
        length = inputs.itemById(MENU_HOOK_GROUP).children.itemById(MENU_HOOK_LENGTH).value
        size = inputs.itemById(MENU_HOOK_GROUP).children.itemById(MENU_HOOK_SIZE).value
        args.areInputsValid = topTrim > 0 and bottomTrim > 0 and length >= 0 and size <= (topTrim + bottomTrim) and size >= 0.75

    if inputs.itemById(MENU_ANCHOR_GROUP).isVisible:
        topOffset = inputs.itemById(MENU_ANCHOR_GROUP).children.itemById(MENU_ANCHOR_TOP_OFFSET).value
        headDiameter = inputs.itemById(MENU_ANCHOR_GROUP).children.itemById(MENU_ANCHOR_HEAD_DIAMETER).value
        countersinkAngle = inputs.itemById(MENU_ANCHOR_GROUP).children.itemById(MENU_ANCHOR_COUNTERSINK_ANGLE).value
        holeDiameter = inputs.itemById(MENU_ANCHOR_GROUP).children.itemById(MENU_ANCHOR_HOLE_DIAMETER).value

        args.areInputsValid = (
            headDiameter > 0
            and countersinkAngle > 0
            and countersinkAngle < 180
            and holeDiameter > 0
            and holeDiameter < headDiameter
            and topOffset < WALL_THICKNESS_CM - WALL_INNER_SECTION_OFFSET_CM - ACC_ANCHOR_TOP_OFFSET_CM
        )


# This event handler is called when the command terminates.
def command_destroy(args: CommandEventArgs):
    global local_handlers
    local_handlers = []


def generateShelf(args: CommandEventArgs):
    """
    Generates a shelf, which is a base wall insert with a shelf insert that snap in it.
    """

    inputs = args.command.commandInputs
    xCount = inputs.itemById(MENU_SHELF_GROUP).children.itemById(MENU_SHELF_X_COUNT).value
    trimTop = inputs.itemById(MENU_SHELF_GROUP).children.itemById(MENU_SHELF_TRIM_TOP).value
    trimBottom = inputs.itemById(MENU_SHELF_GROUP).children.itemById(MENU_SHELF_TRIM_BOTTOM).value
    extraSpacing = inputs.itemById(MENU_SHELF_GROUP).children.itemById(MENU_SHELF_EXTRA_SPACING).value
    notch = inputs.itemById(MENU_SHELF_GROUP).children.itemById(MENU_SHELF_NOTCH).value
    shelfDepth = inputs.itemById(MENU_SHELF_GROUP).children.itemById(MENU_SHELF_DEPTH).value
    shelfLength = inputs.itemById(MENU_SHELF_GROUP).children.itemById(MENU_SHELF_LENGTH).value
    invertAxis = inputs.itemById(MENU_SHELF_GROUP).children.itemById(MENU_SHELF_INVERSE).value

    internalGenerateShelf(insertOuterRadius, xCount, trimTop, trimBottom, extraSpacing, notch, shelfDepth, shelfLength, invertAxis)


def internalGenerateShelf(
    xCount: int, trimTop: float, trimBottom: float, extraSpacing: float, notch: bool, shelfDepth: float, shelfLength: float, invertAxis: bool
):
    # start by genearing the insert
    shelfBaseComponent = generateInsertBase(
        MENU_SHELF,
        insertOuterRadius,
        trimTop,
        trimBottom,
        xCount,
        1,
        extraSpacing,
        notch,
        invertAxis,
    )

    planeInput: ConstructionPlaneInput = shelfBaseComponent.component.constructionPlanes.createInput()
    bottomOffset = trimBottom + GRIDFINITY_BASE_HEIGHT_CM / 2 + GRIDFINITY_Z_OFFSET_CM
    planeInput.setByOffset(shelfBaseComponent.component.xYConstructionPlane, ValueInput.createByReal(-bottomOffset))

    offsetPlane = shelfBaseComponent.component.constructionPlanes.add(planeInput)
    sketches = shelfBaseComponent.component.sketches
    offsetSketch: Sketch = sketches.add(offsetPlane)
    offsetSketch.name = "Shelf"

    shelfThikness = ACC_EXTENSION_HEIGTH_CM / 2
    numFits = int(shelfLength // GRIDFINITY_SIZE_CM)
    sideWidth = (shelfLength - max(xCount - 1, numFits - 1) * GRIDFINITY_SIZE_CM) / 2

    xAxisOffset = GRIDFINITY_SIZE_CM / 2  # because of the adjustment made to match the gridfinity generator, the base insert uses the same code
    x1 = -sideWidth + xAxisOffset
    x2 = max(xCount - 1, numFits - 1) * GRIDFINITY_SIZE_CM + sideWidth + xAxisOffset
    y2 = shelfDepth
    rectangle: SketchLineList = offsetSketch.sketchCurves.sketchLines.addTwoPointRectangle(Point3D.create(x1, 0, 0), Point3D.create(x2, y2, 0))

    ledgeOffset = ACC_LEDGER_WIDTH_CM
    holeOffset = ledgeOffset + ACC_SHELF_WIDTH_CM - ACC_LEDGER_WIDTH_CM
    outterFilletRadius = ACC_INTERNAL_SKETCH_RADIUS_CM + holeOffset
    for l in range(0, rectangle.count):
        # the way the rect is created I need to filter by value here to prevent fillet on back side when can't fit on the front of the insert
        # TODO check for extraHeight, if 0, values change
        filletRadius = outterFilletRadius if l == 1 or l == 2 else min(outterFilletRadius, max(0, sideWidth - ACC_EXTENSION_WIDTH_CM / 2))
        if filletRadius > 0.01:
            offsetSketch.sketchCurves.sketchArcs.addFillet(
                rectangle.item(l),
                rectangle.item(l).startSketchPoint.geometry,
                rectangle.item((l + 1) % rectangle.count),
                rectangle.item((l + 1) % rectangle.count).endSketchPoint.geometry,
                filletRadius,
            )

    shelfThikness = GRIDFINITY_BASE_HEIGHT_CM
    shelfBaseComponent.component.features.extrudeFeatures.addSimple(offsetSketch.profiles.item(0), ValueInput.createByReal(shelfThikness), FeatureOperations.JoinFeatureOperation)
    holeSketch: Sketch = sketches.add(offsetPlane)

    rectWithFillet(
        holeSketch,
        x1 + holeOffset,
        holeOffset,
        0,
        x2 - holeOffset,
        y2 - holeOffset,
        0,
        ACC_INTERNAL_SKETCH_RADIUS_CM,
    )
    shelfBaseComponent.component.features.extrudeFeatures.addSimple(holeSketch.profiles.item(0), ValueInput.createByReal(shelfThikness), FeatureOperations.CutFeatureOperation)

    ledgeSketch: Sketch = sketches.add(offsetPlane)
    ledgeSketch.name = "Shelf Ledge"
    ledgeRadius = ACC_SHELF_WIDTH_CM - ACC_LEDGER_WIDTH_CM + ACC_INTERNAL_SKETCH_RADIUS_CM
    rectWithFillet(ledgeSketch, x1 + ledgeOffset, ledgeOffset, shelfThikness / 2, x2 - ledgeOffset, y2 - ledgeOffset, shelfThikness / 2, ledgeRadius)
    shelfBaseComponent.component.features.extrudeFeatures.addSimple(ledgeSketch.profiles.item(0), ValueInput.createByReal(shelfThikness / 2), FeatureOperations.CutFeatureOperation)

    # creating a sketch to path the notch
    ledgeNotchSketch: Sketch = sketches.add(offsetPlane)
    ledgeNotchSketch.name = "Ledge Notch"
    notchOffset = NOTCH_SIZE_RADIUS_CM
    ledgeLines = rectWithFillet(
        ledgeNotchSketch, x1 + ledgeOffset, ledgeOffset, shelfThikness / 2 + notchOffset, x2 - ledgeOffset, y2 - ledgeOffset, shelfThikness / 2 + notchOffset, ledgeRadius
    )

    startPoint: SketchLine = ledgeNotchSketch.sketchCurves.sketchLines.item(0)

    planes = shelfBaseComponent.component.constructionPlanes
    plane_input = planes.createInput()
    plane_input.setByDistanceOnPath(startPoint, ValueInput.createByReal(0))
    plane = planes.add(plane_input)

    sketch_plane = sketches.add(plane)
    circleCenter = sketch_plane.sketchCurves.sketchCircles.addByCenterRadius(startPoint.geometry.startPoint, notchOffset)

    projectedEdge = sketch_plane.project(startPoint)
    constraints = sketch_plane.geometricConstraints
    constraints.addCoincident(circleCenter.centerSketchPoint, projectedEdge.item(0))

    sweep = shelfBaseComponent.component.features.sweepFeatures
    sweepPath = shelfBaseComponent.component.features.createPath(ledgeLines.item(0))

    sweepInput = sweep.createInput(sketch_plane.profiles.item(0), sweepPath, FeatureOperations.CutFeatureOperation)
    sweepFeature: SweepFeature = sweep.add(sweepInput)
    sweepFeature.name = "Shelf Notch"

    tf = selectFaceAt(shelfBaseComponent.component, offsetPlane, -EXTERNAL_TOLERANCE_CM)
    bf = selectFaceAt(shelfBaseComponent.component, offsetPlane, -shelfThikness - EXTERNAL_TOLERANCE_CM)

    toFillet = ObjectCollection.create()
    for e in tf.edges:
        toFillet.add(e)
    for e in bf.edges:
        toFillet.add(e)
    if sideWidth >= 0.75:  # TODO: Need to exclude the edges that cause issues instead
        filletEdges(shelfBaseComponent.component, toFillet, 0.1)

    # Emboss required shelf insert size
    bottomFace = selectFaceAt(shelfBaseComponent.component, offsetPlane, -bottomOffset)
    textSketch = sketches.add(bottomFace)
    textSketch.name = "Shelf Insert Dimiensions"

    lenText = f"L {((shelfLength - 0.8 - EXTERNAL_TOLERANCE_CM) * 10):05.2f} mm"
    offsetFromSide = 0.525
    lenTextPositionStart = Point3D.create(x1, offsetFromSide, 0)
    lenTextPositionEnd = Point3D.create(-shelfLength - x1, offsetFromSide, 0)
    embossText(shelfBaseComponent.component, textSketch, lenText, lenTextPositionStart, lenTextPositionEnd, -0.05)

    deptText = f"D {((shelfDepth - 0.8 - EXTERNAL_TOLERANCE_CM) * 10):05.2f} mm"
    depthTextPositionStart = Point3D.create(-offsetFromSide - x1, 0, 0)
    depthTextPositionEnd = Point3D.create(-offsetFromSide - x1, shelfDepth, 0)
    embossText(shelfBaseComponent.component, textSketch, deptText, depthTextPositionStart, depthTextPositionEnd, -0.05)


def embossText(targetOccurence: Occurrence, sketch: Sketch, text: str, start: Point3D, end: Point3D, embossHeight: float):
    """
    Embosses the given text along a path in a sketch.

    Args:
        targetOccurence (Occurrence): The target occurrence to add the cut feature to.
        sketch (Sketch): The sketch to create the text and path in.
        text (str): The text to emboss.
        start (Point3D): The starting point of the path.
        end (Point3D): The ending point of the path.
        embossHeight (float): The height of the emboss (how deep the text cut).

    Returns:
        ExtrudeFeature: The created cut feature.
    """

    path = sketch.sketchCurves.sketchLines.addByTwoPoints(start, end)
    texts = sketch.sketchTexts
    input = texts.createInput2(text, 0.35)
    input.textStyle = TextStyles.TextStyleBold
    input.setAsAlongPath(path, False, HorizontalAlignments.CenterHorizontalAlignment, 50)
    input.fontName = "Arial"
    textSketch = texts.add(input)
    return targetOccurence.features.extrudeFeatures.addSimple(textSketch, ValueInput.createByReal(embossHeight), FeatureOperations.CutFeatureOperation)


def rectWithFillet(sketch: Sketch, x1: float, y1: float, z1: float, x2: float, y2: float, z2: float, filletRadius: float) -> ObjectCollection:
    """
    Creates a rectangle with fillet corners in a given sketch.

    Args:
        sketch (Sketch): The sketch in which the rectangle will be created.
        x1 (float): The x-coordinate of the first corner of the rectangle.
        y1 (float): The y-coordinate of the first corner of the rectangle.
        z1 (float): The z-coordinate of the first corner of the rectangle.
        x2 (float): The x-coordinate of the second corner of the rectangle.
        y2 (float): The y-coordinate of the second corner of the rectangle.
        z2 (float): The z-coordinate of the second corner of the rectangle.
        filletRadius (float): The radius of the fillet corners.

    Returns:
        ObjectCollection: A collection of lines and arcs representing the rectangle with fillet corners.
    """

    lines = ObjectCollection.create()
    rect: SketchLineList = sketch.sketchCurves.sketchLines.addTwoPointRectangle(Point3D.create(x1, y1, z1), Point3D.create(x2, y2, z2))

    for l in sketch.sketchCurves.sketchLines:
        lines.add(l)

    for l in range(0, rect.count):
        arc = sketch.sketchCurves.sketchArcs.addFillet(
            rect.item(l), rect.item(l).startSketchPoint.geometry, rect.item((l + 1) % rect.count), rect.item((l + 1) % rect.count).endSketchPoint.geometry, filletRadius
        )
        lines.add(arc)

    return lines


def generateShelfInsert(args: CommandEventArgs):
    """
    Generates a shelf insert component based on the provided arguments.

    Args:
        args (CommandEventArgs): The command arguments.

    Returns:
        None
    """

    inputs = args.command.commandInputs
    notch = inputs.itemById(MENU_SHELF_INSERT_GROUP).children.itemById(MENU_SHELF_INSERT_NOTCH).value
    thickness = inputs.itemById(MENU_SHELF_INSERT_GROUP).children.itemById(MENU_SHELF_INSERT_THICKNESS).value
    shelfDepth = inputs.itemById(MENU_SHELF_INSERT_GROUP).children.itemById(MENU_SHELF_INSERT_DEPTH).value - EXTERNAL_TOLERANCE_CM
    shelfLength = inputs.itemById(MENU_SHELF_INSERT_GROUP).children.itemById(MENU_SHELF_INSERT_LENGTH).value - EXTERNAL_TOLERANCE_CM

    design = app.activeProduct
    root: Component = Component.cast(design.rootComponent)
    shelfInsertComponent = createNamedComponent(root, MENU_SHELF_INSERT)

    sketches = shelfInsertComponent.component.sketches
    xy_plane = shelfInsertComponent.component.xYConstructionPlane
    sketch = sketches.add(xy_plane)

    rectWithFillet(sketch, 0, 0, 0, shelfLength - getClearance(), shelfDepth - getClearance(), 0, ACC_SHELF_WIDTH_CM - ACC_LEDGER_WIDTH_CM + ACC_INTERNAL_SKETCH_RADIUS_CM)
    shelfInsertComponent.component.features.extrudeFeatures.addSimple(sketch.profiles.item(0), ValueInput.createByReal(thickness), FeatureOperations.JoinFeatureOperation)

    face: BRepFace = selectTopFace(shelfInsertComponent.component, xy_plane)
    edgeToFillet = ObjectCollection.create()
    for e in face.edges:
        edgeToFillet.add(e)

    filletEdges(shelfInsertComponent.component, edgeToFillet, 0.1)

    if notch:
        # rotation axis
        axisSketchCenter = Point3D.create(shelfLength / 2, shelfDepth / 2, 0)
        endPoint = Point3D.create(axisSketchCenter.x, axisSketchCenter.y, 1)
        lines = shelfInsertComponent.component.sketches.add(shelfInsertComponent.component.xYConstructionPlane).sketchCurves.sketchLines
        axisLine = lines.addByTwoPoints(axisSketchCenter, endPoint)
        axisLine.isConstruction = True

        # notch
        notchSketchXZ: Sketch = sketches.add(shelfInsertComponent.component.xZConstructionPlane)
        notchSketchCenter1 = Point3D.create(0, -NOTCH_SIZE_RADIUS_CM + getClearance(), 0.5)
        notchSketchCenter2 = Point3D.create(0, -NOTCH_SIZE_RADIUS_CM + getClearance(), shelfDepth - 0.5 - NOTCH_SIZE_RADIUS_CM * 2)
        notchSketchXZ.name = "Notch"

        notchSketchXZ.sketchCurves.sketchCircles.addByCenterRadius(notchSketchCenter1, NOTCH_SIZE_RADIUS_CM - getClearance())
        circPatternSketch(shelfInsertComponent.component, FeatureOperations.JoinFeatureOperation, notchSketchXZ, NOTCH_SIZE_RADIUS_CM * 2, 2, axisLine)
        notchSketchXZ.sketchCurves.sketchCircles.addByCenterRadius(notchSketchCenter2, NOTCH_SIZE_RADIUS_CM - getClearance())
        circPatternSketch(shelfInsertComponent.component, FeatureOperations.JoinFeatureOperation, notchSketchXZ, NOTCH_SIZE_RADIUS_CM * 2, 2, axisLine)

        # notch
        notchSketchYZ: Sketch = sketches.add(shelfInsertComponent.component.yZConstructionPlane)
        notchSketchCenter1 = Point3D.create(-NOTCH_SIZE_RADIUS_CM + getClearance(), 0, 0.5)
        notchSketchCenter2 = Point3D.create(-NOTCH_SIZE_RADIUS_CM + getClearance(), 0, shelfLength - 0.5 - NOTCH_SIZE_RADIUS_CM * 2)
        notchSketchYZ.name = "Notch"

        notchSketchYZ.sketchCurves.sketchCircles.addByCenterRadius(notchSketchCenter1, NOTCH_SIZE_RADIUS_CM - getClearance())
        circPatternSketch(shelfInsertComponent.component, FeatureOperations.JoinFeatureOperation, notchSketchYZ, NOTCH_SIZE_RADIUS_CM * 2, 2, axisLine)
        notchSketchYZ.sketchCurves.sketchCircles.addByCenterRadius(notchSketchCenter2, NOTCH_SIZE_RADIUS_CM - getClearance())
        circPatternSketch(shelfInsertComponent.component, FeatureOperations.JoinFeatureOperation, notchSketchYZ, NOTCH_SIZE_RADIUS_CM * 2, 2, axisLine)

        axisLine.deleteMe()

        # TODO add a hole generator? with patterns


def generateInsert(args: CommandEventArgs):
    """
    Generates an wall insert based on the given command arguments.

    Args:
        args (CommandEventArgs): The command arguments.

    Returns:
        None
    """
    inputs = args.command.commandInputs
    insertXCount = inputs.itemById(MENU_INSERT_GROUP).children.itemById(MENU_INSERT_X_COUNT).value
    insertYCount = inputs.itemById(MENU_INSERT_GROUP).children.itemById(MENU_INSERT_Y_COUNT).value
    trimTop = inputs.itemById(MENU_INSERT_GROUP).children.itemById(MENU_INSERT_TRIM_TOP).value
    trimBottom = inputs.itemById(MENU_INSERT_GROUP).children.itemById(MENU_INSERT_TRIM_BOTTOM).value
    extraSpacing = inputs.itemById(MENU_INSERT_GROUP).children.itemById(MENU_INSERT_EXTRA_SPACING).value
    notch = inputs.itemById(MENU_INSERT_GROUP).children.itemById(MENU_INSERT_NOTCH).value
    invertAxis = inputs.itemById(MENU_INSERT_GROUP).children.itemById(MENU_INSERT_INVERSE).value
    generateInsertBase(MENU_INSERT, trimTop, trimBottom, insertXCount, insertYCount, extraSpacing, notch, invertAxis)


def generateInsertBase(
    name: str, trimTop: float, trimBottom: float, insertXCount: int, insertYCount: int, extraSpacing: float, generateNotch, invertAxis: bool = False
) -> Occurrence:
    """
    Generate the base insert for the accessories.

    Args:
        name (str): The name of the insert component.
        insertOuterRadius (float): The outer radius of the insert.
        trimTop (float): The amount to trim from the top of the insert.
        trimBottom (float): The amount to trim from the bottom of the insert.
        insertXCount (int): The number of inserts in the X direction.
        insertYCount (int): The number of inserts in the Y direction.
        extraSpacing (float): Extra spacing between inserts.
        generateNotch: Whether to generate a notch in the insert.
        invertAxis (bool, optional): Whether to invert the axis. Defaults to False.

    Returns:
        Occurrence: The generated insert component.
    """
    design = app.activeProduct
    root: Component = Component.cast(design.rootComponent)

    insertOuterRadius = getScrewInnerRadius() - getClearance() - 0.05 # 0.5 to give some space

    if trimTop > insertOuterRadius:
        trimTop = insertOuterRadius

    if trimBottom > insertOuterRadius:
        trimBottom = insertOuterRadius

    insertComponent = createNamedComponent(root, name)

    # Based on a XZ plane, so y=z and z=y
    baseHeight = WALL_INNER_SECTION_OFFSET_CM
    xAxisOffset = GRIDFINITY_SIZE_CM / 2
    yAxisOffset = GRIDFINITY_BASE_HEIGHT_CM / 2 + GRIDFINITY_Z_OFFSET_CM  # bases on gridfinity base heigth and an offset of .5mm from xy axis
    zAxisOffset = -baseHeight - MAIN_SCREW_THREAD_BODY_THICKNESS_CM - MAIN_SCREW_THREAD_BODY_THICKNESS_CM - EXTERNAL_TOLERANCE_CM - extraSpacing

    # base of the insert
    centerPoint = Point3D.create(xAxisOffset, yAxisOffset, zAxisOffset)
    createCylinderFromPointXZPlane(insertComponent.component, insertOuterRadius, baseHeight, centerPoint)

    offset = baseHeight
    insertChamfer = createCylinderFromPointXZPlane(
        insertComponent.component,
        insertOuterRadius - MAIN_SCREW_THREAD_BODY_THICKNESS_CM / 2,
        MAIN_SCREW_THREAD_BODY_THICKNESS_CM,
        Point3D.create(xAxisOffset, yAxisOffset, zAxisOffset + offset),
    )

    # Chamfer
    chamfers = root.features.chamferFeatures
    chamferInput = chamfers.createInput2()
    chamferInput.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
        wrapInCollection(insertChamfer.endFaces.item(0).edges.item(0)), ValueInput.createByReal(MAIN_SCREW_THREAD_BODY_THICKNESS_CM), False
    )
    chamfer = chamfers.add(chamferInput)

    offset += MAIN_SCREW_THREAD_BODY_THICKNESS_CM
    createCylinderFromPointXZPlane(
        insertComponent.component,
        MAIN_SCREW_HEAD_INTERNAL_DIAMETER_CM / 2 - EXTERNAL_TOLERANCE_CM,
        MAIN_SCREW_THREAD_BODY_THICKNESS_CM + EXTERNAL_TOLERANCE_CM,
        Point3D.create(xAxisOffset, yAxisOffset, zAxisOffset + offset),
    )

    sketches = insertComponent.component.sketches
    xz_plane = insertComponent.component.xZConstructionPlane

    if extraSpacing > 0:
        sketche = sketches.add(xz_plane)
        sketche.name = "Extra Spacing"
        create2PointRectFromPoints(
            insertComponent,
            sketche,
            Point3D.create(-ACC_EXTENSION_WIDTH_CM / 2 + xAxisOffset, -ACC_EXTENSION_HEIGTH_CM / 2 + yAxisOffset, -extraSpacing),
            Point3D.create(ACC_EXTENSION_WIDTH_CM / 2 + xAxisOffset, ACC_EXTENSION_HEIGTH_CM / 2 + yAxisOffset, -extraSpacing),
            extraSpacing,
        )

        # This is causing issues and I'm not convinced it's adding value
        # edgeToFillet = ObjectCollection.create()
        # for f in rect.faces:
        #     for e in f.edges:
        #         if math.isclose(e.pointOnEdge.y, -yAxisOffset, abs_tol=0.01):
        #             edgeToFillet.add(e)

        # filletEdges(insertComponent.component, edgeToFillet, 0.1)

    if generateNotch:
        createNotch(insertComponent.component, insertOuterRadius, invertAxis, zAxisOffset, centerPoint)

    # trimming the sides of the insert so it can be inserted in the screw
    if trimTop < insertOuterRadius:
        cuttingInsertSide(
            insertComponent.component,
            sketches.add(xz_plane),
            trimTop,
            MAIN_SCREW_THREAD_BODY_THICKNESS_CM + EXTERNAL_TOLERANCE_CM + offset + extraSpacing,
            xAxisOffset,
            yAxisOffset,
            False,
            invertAxis,
        )
    if trimBottom < insertOuterRadius:
        cuttingInsertSide(
            insertComponent.component,
            sketches.add(xz_plane),
            trimBottom,
            MAIN_SCREW_THREAD_BODY_THICKNESS_CM + EXTERNAL_TOLERANCE_CM + offset + extraSpacing,
            xAxisOffset,
            yAxisOffset,
            True,
            invertAxis,
        )

    if insertXCount > 1 or insertYCount > 1:
        xAxis = insertComponent.component.xConstructionAxis
        patternInsertSection(insertComponent.component, xAxis, wrapInCollection(insertComponent.bRepBodies.item(0)), insertXCount)

        offset_angle = calculateOffsetAngle(WALL_NB_SIDES)
        r = GRIDFINITY_SIZE_CM / 2 / math.cos(math.pi / WALL_NB_SIDES)
        for rowIndex in range(1, insertYCount):
            startPoint = createHexPoint(r, HexPointIndex.TOP.value, offset_angle)
            toPoint = createHexPoint(r, HexPointIndex.BOTTOM_LEFT.value if rowIndex % 2 == 0 else HexPointIndex.BOTTOM_RIGHT.value, offset_angle)
            delta = createDeltaVector(startPoint, toPoint)
            copyBodies(insertComponent.component, wrapInCollection(insertComponent.bRepBodies.item(0)), delta)
            patternBodies(insertComponent.component, xAxis, wrapInCollection(insertComponent.bRepBodies.item(0)), insertXCount)

    return insertComponent

def generateHook(args: CommandEventArgs):
 
    inputs = args.command.commandInputs

    trimTop = inputs.itemById(MENU_HOOK_GROUP).children.itemById(MENU_HOOK_TRIM_TOP).value
    trimBottom = inputs.itemById(MENU_HOOK_GROUP).children.itemById(MENU_HOOK_TRIM_BOTTOM).value
    notch = inputs.itemById(MENU_HOOK_GROUP).children.itemById(MENU_HOOK_NOTCH).value
    length = inputs.itemById(MENU_HOOK_GROUP).children.itemById(MENU_HOOK_LENGTH).value
    size = inputs.itemById(MENU_HOOK_GROUP).children.itemById(MENU_HOOK_SIZE).value
    
    addStopper = inputs.itemById(MENU_HOOK_GROUP).children.itemById(MENU_HOOK_STOPPER).value
    stopperHeight = inputs.itemById(MENU_HOOK_GROUP).children.itemById(MENU_HOOK_STOPPER_HEIGHT).value

    # start by genearing the insert
    baseComponent = generateInsertBase(MENU_HOOK, trimTop, trimBottom, 1, 1, 0, notch, True)

    planeInput: ConstructionPlaneInput = baseComponent.component.constructionPlanes.createInput()
    zAxisOffset = WALL_INNER_SECTION_OFFSET_CM - MAIN_SCREW_THREAD_BODY_THICKNESS_CM - MAIN_SCREW_THREAD_BODY_THICKNESS_CM
    planeInput.setByOffset(baseComponent.component.xZConstructionPlane, ValueInput.createByReal(zAxisOffset))

    offsetPlane = baseComponent.component.constructionPlanes.add(planeInput)
    sketches = baseComponent.component.sketches
    offsetSketch: Sketch = sketches.add(offsetPlane)
    offsetSketch.name = "Hook"

    xAxisOffset = GRIDFINITY_SIZE_CM / 2
    centerBottomOffset = -(GRIDFINITY_Z_OFFSET_CM + trimBottom)
    bottomOffset = centerBottomOffset - trimBottom + size / 2
    if size > trimBottom * 2:
        bottomOffset = centerBottomOffset + (size - trimBottom * 2) / 2
    createPolygon(offsetSketch, size / 2, 8, -xAxisOffset, bottomOffset)

    extrudes = baseComponent.component.features.extrudeFeatures
    extrude_input = extrudes.createInput(offsetSketch.profiles.item(0), FeatureOperations.NewBodyFeatureOperation)
    extrude_distance = ValueInput.createByReal(length)
    extrude_input.setDistanceExtent(False, extrude_distance)
    hookExtrusion: ExtrudeFeature = extrudes.add(extrude_input)

    if addStopper:
        stopperPlaneInput: ConstructionPlaneInput = baseComponent.component.constructionPlanes.createInput()

        if size > trimBottom * 2:
            sizeOffset =  (trimBottom * 2 - size)
        else:
            sizeOffset =  -(-trimBottom * 2 + size)

        stopperPlaneInput.setByOffset(baseComponent.component.xYConstructionPlane, ValueInput.createByReal(-GRIDFINITY_Z_OFFSET_CM - sizeOffset))
        stopperPlane = baseComponent.component.constructionPlanes.add(stopperPlaneInput)
        sketches = baseComponent.component.sketches

        stopperRadius = (size / 2 - 0.15) / 2
        stopperCenter = Point3D.create(xAxisOffset, length - stopperRadius - 0.05, 0)
        stopper = createCylinderFromPoint(stopperPlane.component, stopperRadius, stopperHeight, stopperCenter, stopperPlane)

        for face in stopper.endFaces:
            for e in face.edges:
                filletEdges(baseComponent.component, wrapInCollection(e), 0.2 if size > 8 else 0.1)

    # select the edges that match the length, so we know it's the side edges
    edges = ObjectCollection.create()
    for face in hookExtrusion.faces:
        for e in face.edges:
            if e.length == length and not edges.contains(e):
                edges.add(e)

    for face in hookExtrusion.endFaces:
        for e in face.edges:
            edges.add(e)

    # fillet the collection
    filletEdges(baseComponent.component, edges, 0.1)


def createHexPoint(radius: float, index: int, offset_angle: float) -> Point3D:
    """
    Creates a 3D point on a hexagonal shape given the radius, index, and offset angle.

    Args:
        radius (float): The radius of the hexagonal shape.
        index (int): The index of the point on the hexagonal shape.
        offset_angle (float): The offset angle to adjust the position of the point.

    Returns:
        Point3D: The 3D point on the hexagonal shape.
    """
    angle = 2 * math.pi * index / WALL_NB_SIDES - offset_angle
    return Point3D.create(math.cos(angle) * radius, 0, math.sin(angle) * radius)


def createNotch(targetOccurence: Occurrence, insertOuterRadius: float, invertAxis: bool, offset: float, centerPoint: Point3D):
    """
    Creates a notch on a target occurrence to "lock" to the wall. These notches are angles at 45 degrees.

    Args:
        targetOccurence (Occurrence): The target occurrence on which the notch will be created.
        insertOuterRadius (float): The outer radius of the insert.
        invertAxis (bool): Flag indicating whether to invert the axis.
        offset (float): The offset value.
        centerPoint (Point3D): The center point of the notch.

    Returns:
        None
    """

    sketches = targetOccurence.sketches
    if invertAxis:
        plane = targetOccurence.yZConstructionPlane
        notchSketchCenter = Point3D.create(ACC_EXTENSION_HEIGTH_CM / 2 + NOTCH_SIZE_RADIUS_CM / 2, offset, GRIDFINITY_SIZE_CM / 2 - insertOuterRadius + NOTCH_SIZE_RADIUS_CM)
    else:
        plane = targetOccurence.xYConstructionPlane
        notchSketchCenter = Point3D.create(GRIDFINITY_SIZE_CM / 2, offset, ACC_EXTENSION_HEIGTH_CM / 2 + NOTCH_SIZE_RADIUS_CM / 2)

    endPoint = Point3D.create(centerPoint.x, centerPoint.y, 0)
    lines = targetOccurence.sketches.add(targetOccurence.xZConstructionPlane).sketchCurves.sketchLines
    axisLine = lines.addByTwoPoints(centerPoint, endPoint)
    axisLine.isConstruction = True

    sketch: Sketch = sketches.add(plane)
    sketch.name = "Notch"
    sketch.sketchCurves.sketchCircles.addByCenterRadius(notchSketchCenter, NOTCH_SIZE_RADIUS_CM - getClearance())
    circPatternSketch(targetOccurence, FeatureOperations.JoinFeatureOperation, sketch, NOTCH_SIZE_RADIUS_CM * 2, 2, axisLine)
    axisLine.deleteMe()  # gives warning


def patternInsertSection(rootComponent: Component, xAxis, bodies: ObjectCollection, width: int) -> RectangularPatternFeatures:
    """
    Generates a rectangular an horizontal pattern of insert sections. This pattern match the wall grid and
    can be used to build accossories without worrying about them fitting in the wall.

    Args:
        rootComponent (Component): The root component of the assembly.
        xAxis: The X-axis direction for the pattern.
        bodies (ObjectCollection): The collection of bodies to be patterned.
        width (int): The width of the pattern.

    Returns:
        RectangularPatternFeatures: The generated rectangular pattern features.
    """
    quantityOne = ValueInput.createByReal(width)
    distanceOne = ValueInput.createByReal(GRIDFINITY_SIZE_CM)

    # Generate a row of insert
    rectangularPatterns = rootComponent.features.rectangularPatternFeatures
    rectangularPatternInput = rectangularPatterns.createInput(bodies, xAxis, quantityOne, distanceOne, PatternDistanceType.SpacingPatternDistanceType)
    return rectangularPatterns.add(rectangularPatternInput)


def cuttingInsertSide(targetOccurence: Occurrence, cuttingSketch, insertWidth: float, height: float, xOffset, yOffset, reverse: bool, invertAxis: bool = False):
    """
    Removes sides of inserts. It's usefull to have a bottom trimmed to better print flat without support.
    The invert axis when the insert is rotated 90 degrees.

    Args:
        targetOccurence (Occurrence): The target occurrence to apply the cutting feature to.
        cuttingSketch: The sketch used for creating the cutting feature.
        insertWidth (float): The width of the insert.
        height (float): The height of the cutting feature.
        xOffset: The x-offset of the cutting feature.
        yOffset: The y-offset of the cutting feature.
        reverse (bool): Determines whether to reverse the insert width and height.
        invertAxis (bool, optional): Determines whether to invert the x and y axes. Defaults to False.
    """

    if invertAxis:
        cuttingSketch.sketchCurves.sketchLines.addTwoPointRectangle(
            Point3D.create(-getScrewInnerRadius() + xOffset, insertWidth + yOffset if reverse else -insertWidth + yOffset, 0),
            Point3D.create(getScrewInnerRadius() + xOffset, getScrewInnerRadius() + yOffset if reverse else -getScrewInnerRadius() + yOffset, 0),
        )
    else:
        cuttingSketch.sketchCurves.sketchLines.addTwoPointRectangle(
            Point3D.create(insertWidth + xOffset if reverse else -insertWidth + xOffset, -getScrewInnerRadius() + yOffset, 0),
            Point3D.create(getScrewInnerRadius() + xOffset if reverse else -getScrewInnerRadius() - xOffset, getScrewInnerRadius() + yOffset, 0),
        )

    profile = cuttingSketch.profiles.item(0)
    extrudes = targetOccurence.features.extrudeFeatures
    cutterInput = extrudes.createInput(profile, FeatureOperations.CutFeatureOperation)
    cutterInput.setDistanceExtent(False, ValueInput.createByReal(-height))  # Use the same distance as the outer extrusion
    extrudes.add(cutterInput)


def anchorCommonBase(anchorOccurrence: Occurrence, height: float, clearance: float) -> ExtrudeFeature:
    """
    Creates an anchor base for the given anchor occurrence.

    Args:
        anchorOccurrence (Occurrence): The anchor occurrence to create the base for.
        height (float): The height of the anchor base.
        clearance (float): The clearance value for the anchor base.

    Returns:
        ExtrudeFeature: The created anchor base.

    """
    internalRadius = GRIDFINITY_SIZE_CM / 2 - WALL_OUTER_WALL_THICKNESS_CM - WALL_INNER_WALL_OFFSET_CM - WALL_INNER_WALL_OFFSET_CM

    # Based on wall thickness and the chamfer angle, calculate the chamfer width
    internalSectionHeight = WALL_THICKNESS_CM - WALL_INNER_SECTION_OFFSET_CM - 0.1
    chamferOffset = calculateChamferWidth(INTERNAL_WALL_CHAMFER_ANGLE, internalSectionHeight)
    radius = internalRadius + chamferOffset - clearance / 2

    anchorBase = createCylinder(anchorOccurrence.component, radius, height)
    anchorBase.name = "Anchor Base"
    # no space as this is the body that will be exported to a file and I don't like spaces in file names
    anchorOccurrence.component.bRepBodies.item(0).name = "AnchorBase"

    # Chamfer the anchor so it fits into the wall
    createAnchorChamfer(anchorOccurrence, anchorBase.faces.item(0).edges.item(1), height, True)
    return anchorBase


def generateAnchor(args: CommandEventArgs, offsetAnchor: bool = False):
    """
    Generates an anchor component based on the provided arguments.

    Args:
        args (CommandEventArgs): The command arguments.
        offsetAnchor (bool, optional): Whether to offset the anchor. Defaults to False.
    """

    design = app.activeProduct
    root: Component = Component.cast(design.rootComponent)

    clearance = getClearance()
    height = WALL_THICKNESS_CM - WALL_INNER_SECTION_OFFSET_CM - clearance

    anchorComponent: Occurrence = createNamedComponent(root, MENU_ANCHOR)
    anchorBase: ExtrudeFeature = anchorCommonBase(anchorComponent, height, clearance)

    if offsetAnchor:
        # Offset insert curring and genration
        chamferWidth = height / math.tan(math.radians(INTERNAL_WALL_CHAMFER_ANGLE))
        innerCutRadius = MAIN_SCREW_HEAD_INTERNAL_DIAMETER_CM / 2 * 0.65 + EXTERNAL_TOLERANCE_CM
        offsetLocation = Point3D.create(innerCutRadius / 2 - chamferWidth, 0, 0)

        # inner offset part
        offsetAnchor = createCylinderFromPointXYPlane(anchorComponent.component, innerCutRadius, height, offsetLocation, FeatureOperations.NewBodyFeatureOperation)
        chamferedInsert = createAnchorChamfer(anchorComponent, offsetAnchor.faces.item(0).edges.item(1), height, True)

        # Cut the main part with the offset insert
        combineFeatures = root.features.combineFeatures
        tools = ObjectCollection.create()
        tools.add(chamferedInsert.bodies.item(0))
        input: CombineFeatureInput = combineFeatures.createInput(anchorBase.bodies.item(0), tools)
        input.isNewComponent = False
        input.isKeepToolBodies = False
        input.operation = FeatureOperations.CutFeatureOperation
        combineFeatures.add(input)

        # inner offset part
        offsetAnchor = createCylinderFromPointXYPlane(anchorComponent.component, innerCutRadius, height, offsetLocation, FeatureOperations.NewBodyFeatureOperation)
        offsetAnchor.name = "Anchor Offset Insert"
        # no space as this is the body that will be exported to a file and I don't like spaces in file names
        anchorComponent.component.bRepBodies.item(1).name = "AnchorOffsetInsert"

        createAnchorChamfer(anchorComponent, offsetAnchor.faces.item(0).edges.item(1), height, True)

    inputs = args.command.commandInputs
    topOffset: float = inputs.itemById(MENU_ANCHOR_GROUP).children.itemById(MENU_ANCHOR_TOP_OFFSET).value
    headDiameter: float = inputs.itemById(MENU_ANCHOR_GROUP).children.itemById(MENU_ANCHOR_HEAD_DIAMETER).value
    countersinkAngle: int = inputs.itemById(MENU_ANCHOR_GROUP).children.itemById(MENU_ANCHOR_COUNTERSINK_ANGLE).value
    holeDiameter: float = inputs.itemById(MENU_ANCHOR_GROUP).children.itemById(MENU_ANCHOR_HOLE_DIAMETER).value
    createScrewHole(anchorComponent, anchorBase.endFaces.item(0), headDiameter, countersinkAngle, holeDiameter, topOffset)


def createScrewHole(anchorOccurrence: Occurrence, endFace: BRepFace, headDiameter: float, countersinkAngle: float, holeDiameter: float, topOffset: float):
    """
    Creates a screw hole on the given anchor occurrence.

    Args:
        anchorOccurrence (Occurrence): The anchor occurrence on which the screw hole will be created.
        endFace (BRepFace): The end face of the anchor occurrence.
        headDiameter (float): The diameter of the screw head.
        countersinkAngle (float): The angle of the countersink.
        holeDiameter (float): The diameter of the screw hole.
        topOffset (float): The offset from the top of the anchor occurrence.

    Returns:
        None
    """

    # TODO Add an option to offset the hole from the ceter to support different screw types and be closer to the side of the insert
    sketches = anchorOccurrence.component.sketches
    offsetPlane = createOffsetPlane(anchorOccurrence, endFace, 0)

    if topOffset > 0:
        offsetPoint = Point3D.create(0, 0, WALL_THICKNESS_CM - WALL_INNER_SECTION_OFFSET_CM - getClearance() - topOffset)
        createCylinderFromPointXYPlane(anchorOccurrence.component, headDiameter / 2, topOffset, offsetPoint, FeatureOperations.CutFeatureOperation)

    offsetSketch = sketches.add(offsetPlane)
    offsetSketchPoints = offsetSketch.sketchPoints
    sPt0 = offsetSketchPoints.add(Point3D.create(0, 0, -topOffset))

    hole: HoleFeatures = anchorOccurrence.component.features.holeFeatures
    holeInput = hole.createSimpleInput(ValueInput.createByReal(holeDiameter))
    holeInput.setPositionBySketchPoints(wrapInCollection(sPt0))
    distance = ValueInput.createByReal(WALL_THICKNESS_CM - WALL_INNER_SECTION_OFFSET_CM)
    holeInput.setDistanceExtent(distance)
    screwHole: HoleFeature = hole.add(holeInput)
    screwHole.timelineObject.rollTo(True)
    screwHole.setToCountersink(ValueInput.createByReal(headDiameter), ValueInput.createByReal(countersinkAngle))
    screwHole.timelineObject.rollTo(False)


def generateMainScrew(args: CommandEventArgs):
    """
    Generates the main screw component with body, thread, and head.

    Args:
        args (CommandEventArgs): The command event arguments.

    Returns:
        None
    """

    design = app.activeProduct
    root: Component = Component.cast(design.rootComponent)

    mainScrewComponent = createNamedComponent(root, MENU_MAIN_SCREW)

    mainScrewBodyRadius = getScrewOuterRadius()

    # Screw Body
    inputs = args.command.commandInputs
    bodyHeight: float = inputs.itemById(MENU_MAIN_SCREW_GROUP).children.itemById(MAIN_SCREW_HEIGHT).value
    createMainScrewBody(mainScrewComponent.component, mainScrewBodyRadius, getScrewInnerRadius(), bodyHeight)

    # Screw Thread
    mainScrewThread = createExternalThread(
        mainScrewComponent.component,
        MAIN_SCREW_HEAD_THICKNESS_CM / 2,  # threadStartOffset
        mainScrewBodyRadius,  # radius
        bodyHeight,
    )

    facesForFillet = None
    for b in mainScrewComponent.component.bRepBodies:
        for f in b.faces:
            if math.isclose(f.pointOnFace.z, bodyHeight, abs_tol=0.01):
                facesForFillet = f

    # Create SplitBodyFeatureInput
    splitBodyFeats = root.features.splitBodyFeatures
    splitBodyInput = splitBodyFeats.createInput(mainScrewThread.bodies.item(0), facesForFillet, True)

    # Create split body feature
    splitedBodies = splitBodyFeats.add(splitBodyInput)
    for s in splitedBodies.bodies:
        if s.name == "Body2":
            # just hides the body
            s.isVisible = False

    filletEdges(root, wrapInCollection(facesForFillet.edges.item(0)), 0.05)

    # Screw Head
    createScrewHead(mainScrewComponent)


def createMainScrewBody(targetOccurence: Occurrence, outerSize: float, innerSize: float, height: float) -> ExtrudeFeature:
    """
    Creates a main screw body by extruding a cylinder with a hole.

    Args:
        targetOccurence (Occurrence): The target occurrence where the screw body will be created.
        outerSize (float): The size of the outer circle of the screw body.
        innerSize (float): The size of the inner circle of the screw body.
        height (float): The height of the screw body.

    Returns:
        ExtrudeFeature: The created extrude feature representing the main screw body.
    """

    sketches = targetOccurence.sketches
    xy_plane = targetOccurence.xYConstructionPlane

    # Create a sketch for the outer circle
    outer_sketch = sketches.add(xy_plane)
    outer_sketch.sketchCurves.sketchCircles.addByCenterRadius(Point3D.create(0, 0, 0), outerSize)

    # Create a second sketch for the inner circle
    inner_sketch = sketches.add(xy_plane)
    inner_sketch.sketchCurves.sketchCircles.addByCenterRadius(Point3D.create(0, 0, 0), innerSize)

    # Create a profile from the outer circle
    outer_profile = outer_sketch.profiles.item(0)

    # Create an extrusion for the cylinder
    extrudes = targetOccurence.features.extrudeFeatures
    extrude_input = extrudes.createInput(outer_profile, FeatureOperations.NewBodyFeatureOperation)
    extrude_distance = ValueInput.createByReal(height)
    extrude_input.setDistanceExtent(False, extrude_distance)
    extrudes.add(extrude_input)

    # Create a profile from the inner circle
    inner_profile = inner_sketch.profiles.item(0)

    # Create a second extrusion to remove material and create the hole
    hole_extrude_input = extrudes.createInput(inner_profile, FeatureOperations.CutFeatureOperation)
    hole_extrude_input.setDistanceExtent(False, extrude_distance)  # Use the same distance as the outer extrusion
    return extrudes.add(hole_extrude_input)


def createScrewHead(mainScrewComponent: Occurrence):
    """
    Creates a screw head for the given main screw component.

    Args:
        mainScrewComponent (Occurrence): The main screw component.

    Returns:
        None
    """

    sketches = mainScrewComponent.component.sketches
    yzPlane = mainScrewComponent.component.yZConstructionPlane
    sketch = sketches.add(yzPlane)
    sketch.name = "Screw Head"

    exteriorScrewRadius = (GRIDFINITY_SIZE_CM - HEAD_OFFSET_CM) / 2
    # Draw the main screw profile
    lines = sketch.sketchCurves.sketchLines
    startingPoint = Point3D.create(-MAIN_SCREW_THREAD_BODY_THICKNESS_CM, MAIN_SCREW_HEAD_INTERNAL_DIAMETER_CM / 2, 0)
    internalScrewSide = lines.addByTwoPoints(startingPoint, Point3D.create(0, MAIN_SCREW_HEAD_INTERNAL_DIAMETER_CM / 2, 0))
    bottomLine = lines.addByTwoPoints(internalScrewSide.endSketchPoint, Point3D.create(0, exteriorScrewRadius, 0))
    externalScrewSide = lines.addByTwoPoints(bottomLine.endSketchPoint, Point3D.create(-MAIN_SCREW_HEAD_THICKNESS_CM, bottomLine.endSketchPoint.geometry.y, 0))
    topLine = lines.addByTwoPoints(
        externalScrewSide.endSketchPoint,
        Point3D.create(-MAIN_SCREW_HEAD_THICKNESS_CM, MAIN_SCREW_HEAD_INTERNAL_DIAMETER_CM / 2 + MAIN_SCREW_THREAD_BODY_THICKNESS_CM, 0),
    )
    lines.addByTwoPoints(topLine.endSketchPoint, startingPoint)

    # revolve the sketch now
    rotationAxis = lines.addByTwoPoints(Point3D.create(0, 0, 0), Point3D.create(-1, 0, 0))  # we are working from yz plane, so rotation axis is on X, Y
    rotationAxis.isConstruction = True
    rev_input = mainScrewComponent.component.features.revolveFeatures.createInput(sketch.profiles.item(0), rotationAxis, FeatureOperations.JoinFeatureOperation)
    rev_input.setAngleExtent(False, ValueInput.createByReal(360))
    mainScrewComponent.component.features.revolveFeatures.add(rev_input)

    # pattern the screw head
    xyPlane = mainScrewComponent.component.xYConstructionPlane
    sketch = sketches.add(xyPlane)
    numberOfSlots = 8
    angle = 360 / (numberOfSlots * 2)  # 8 slots + 8 spaces
    slotsWidth = 0.275
    bottomSlotWidth = 0.15
    hardCodedOffset = 0.015
    # the length needs to account for the arc at the end of end of the slot, twice, so removing slotsWidth ( 2 * slotsWidth / 2 = slotsWidth at radius in radian)
    slotLengthInRad = math.pi / 180 * angle - (slotsWidth / exteriorScrewRadius)
    slot(sketch, hardCodedOffset + exteriorScrewRadius - slotsWidth, slotLengthInRad, slotsWidth)  # top slot
    slot(sketch, hardCodedOffset + exteriorScrewRadius - bottomSlotWidth + 0.01, slotLengthInRad * 3 / 4, bottomSlotWidth, MAIN_SCREW_HEAD_THICKNESS_CM / 2)  # bottom slot to loft
    sketch.isVisible = False

    loftFeats = mainScrewComponent.component.features.loftFeatures
    loftInput = loftFeats.createInput(FeatureOperations.CutFeatureOperation)
    loftInput.loftSections.add(sketch.profiles.item(0))
    loftInput.loftSections.add(sketch.profiles.item(1))
    loft: LoftFeature = loftFeats.add(loftInput)

    # pattern the slot around the head
    circularFeats = mainScrewComponent.component.features.circularPatternFeatures
    circularFeatInput = circularFeats.createInput(wrapInCollection(loft), rotationAxis)
    circularFeatInput.quantity = ValueInput.createByReal(numberOfSlots)
    circularFeatInput.totalAngle = ValueInput.createByReal(math.pi * 2)  # full circle
    circularFeat: CircularPatternFeature = circularFeats.add(circularFeatInput)

    # fillet the heads and the patterns
    edgesForFillet = ObjectCollection.create()
    for body in circularFeat.bodies:
        for edge in body.edges:
            edgesForFillet.add(edge)
    try:
        filletEdges(mainScrewComponent.component, edgesForFillet, 0.04)
    except RuntimeError:
        futil.log(f"{CMD_NAME} Failed to fillet the edges:\n{traceback.format_exc()}")


def slot(sketch: Sketch, innerRadius: float, slotLengthInRad: float, slotWidth: float, zOffset: float = 0):
    """
    Creates a the shape in the screw head for creating slots.

    Parameters:
    - sketch: The sketch object where the slot will be created.
    - innerRadius: The inner radius of the slot.
    - slotLengthInRad: The length of the slot in radians.
    - slotWidth: The width of the slot.
    - zOffset: The z-offset of the slot (default is 0).

    Returns:
    None
    """

    arcs = sketch.sketchCurves.sketchArcs
    startOffset = -slotLengthInRad / 2
    internalArc = arcs.addByCenterStartSweep(Point3D.create(0, 0, zOffset), createPoint(innerRadius, startOffset, zOffset), slotLengthInRad)
    externalArc = arcs.addByCenterStartSweep(Point3D.create(0, 0, zOffset), createPoint(innerRadius + slotWidth, startOffset, zOffset), slotLengthInRad)

    firstArcCenterPoint = createPoint(innerRadius + slotWidth / 2, startOffset, zOffset)
    arcs.addByCenterStartSweep(firstArcCenterPoint, internalArc.startSketchPoint, math.pi)
    secondArcCenterPoint = createPoint(innerRadius + slotWidth / 2, slotLengthInRad + startOffset, zOffset)
    arcs.addByCenterStartSweep(secondArcCenterPoint, externalArc.endSketchPoint, math.pi)


def createPoint(radius: float, radian: float, offset: float = 0):
    """
    Creates a 3D point based on the given radius, radian, and offset values.

    Args:
        radius (float): The radius of the point.
        radian (float): The radian value of the point.
        offset (float, optional): The offset value of the point. Defaults to 0.

    Returns:
        Point3D: The created 3D point.
    """
    return Point3D.create(radius * math.cos(radian), radius * math.sin(radian), offset)


def getClearance():
    """
    Get the clearance value for the accessories.

    If a custom clearance input is provided, it will be used instead of the default value.

    Returns:
        float: The clearance value in centimeters.
    """
    clearance = MAIN_SCREW_BODY_CLEARANCE_CM
    global clearanceInput
    if clearanceInput:
        clearance = clearanceInput.value
    return clearance


def getScrewOuterRadius():
    """
    Calculate the outer radius of the main screw.

    Returns:
        float: The outer radius of the screw.
    """
    return (THREAD_SIZE_D_MAJOR_CM - H_NEW_CM - getClearance()) / 2


def getScrewInnerRadius():
    """
    Calculate the inner radius of the main screw.

    This function calculates the inner radius of the main screw by subtracting half of the main screw head thickness from the outer radius.

    Returns:
        float: The inner radius of the screw.
    """
    return getScrewOuterRadius() - MAIN_SCREW_HEAD_THICKNESS_CM / 2
