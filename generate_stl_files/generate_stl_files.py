import threading
import traceback

import adsk.cam
import adsk.core
import adsk.fusion

CALLBACK_NAME = "scriptGenerateWall"


def run(context):
    ui = None
    basePath = "/Users/seb/stl_files/"  # create a input dialog for this

    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        exportPathParamValue = basePath
        addin_thread = threading.Thread(target=stl_wall_generation)
        addin_thread.start()

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
        design.userParameters.itemByName("script_exportPath").comment = "<paht>"
        cmdDef.execute()


def log(msg: str):
    app = adsk.core.Application.get()
    app.log(msg, adsk.core.LogLevels.InfoLogLevel, adsk.core.LogTypes.ConsoleLogType)
