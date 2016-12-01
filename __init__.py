import platform
from getProcessor import *

SM_VERSION = "v0.0.1"

print("SimpleMon " + SM_VERSION)

print("Getting Host Details")

hostDetails = {}
hostDetails["os"] = platform.system() + " " + platform.release()
hostDetails["arch"] = platform.architecture()[0]
hostDetails["processor"] = getProcessor()

print(hostDetails)

