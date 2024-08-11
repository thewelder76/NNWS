import threading
import traceback

import adsk.cam
import adsk.core
import adsk.fusion

CALLBACK_NAME = "scriptGenerateWall"

base_path = "<path>"


def run(context):
    ui = None
    global base_path

    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        folder_dialog = ui.createFolderDialog()
        folder_dialog.title = "Select a Folder"
        folder_dialog.isMultiSelectEnabled = False

        dialog_result = folder_dialog.showDialog()
        if dialog_result == adsk.core.DialogResults.DialogOK:
            base_path = folder_dialog.folder
            addin_thread = threading.Thread(target=stl_wall_generation)
            addin_thread.start()

        else:
            ui.messageBox("Not running script, no directory selected.")

    except:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))


def stl_wall_generation():
    app = adsk.core.Application.get()
    ui = app.userInterface
    cmdDef = ui.commandDefinitions.itemById(CALLBACK_NAME)
    if cmdDef:
        app.log("calling addin...", adsk.core.LogLevels.InfoLogLevel, adsk.core.LogTypes.ConsoleLogType)

        design = app.activeProduct
        design.userParameters.itemByName("script_exportPath").comment = base_path
        cmdDef.execute()


def log(msg: str):
    app = adsk.core.Application.get()
    app.log(msg, adsk.core.LogLevels.InfoLogLevel, adsk.core.LogTypes.ConsoleLogType)
