import platform     # Platform data, such as OS type, release, etc
import subprocess   # Used for running local console commands
import sys          # Used to determine system python version, as we need Python 3 and not 2
import logging      # Well, it's used for logging. Importing it as l because I'm lazy and don't want to type logging everytime.
import uuid         # to distinguish hosts
from tornado.ioloop import IOLoop  # all the tornado stuff is networking
from tornado import gen
from tornado.tcpclient import TCPClient
import ssl          # for encrypted netwoorking
import os           # useful for finding current directory across OSes.
import json         # for encoding network traffic in a sane format

# Make sure we've got Python 3 here, or else weird errors will happen
'''
http://stackoverflow.com/questions/446052/how-can-i-check-for-python-version-in-a-program-that-uses-new-language-features
'''

req_version = (3, 0)  # Require python 3 at minimum
cur_version = sys.version_info

if cur_version >= req_version:
    pass
else:
    print("Your Python interpreter is too old. Simplemon requires at least Python 3.")
    sys.exit(1)  # Generally used to signify an error has occurred on Unix/POSIX systems.


def getProcessor():
    '''
    http://stackoverflow.com/questions/4842448/getting-processor-information-in-python
    http://stackoverflow.com/questions/18244126/python3-subprocess-output
    Returns "Intel(R) Core(TM) i7-4790K CPU @ 4.00GHz Intel64 Family 6 Model 60 Stepping 3, GenuineIntel"
    instead of
    "Intel64 Family 6 Model 60 Stepping 3, GenuineIntel"

    https://docs.python.org/2/library/string.html
    '''
    if platform.system() == "Windows":
        name = subprocess.getoutput(["wmic", "cpu", "get", "name"]).split("\n")[2].strip()
        return name
    elif platform.system() == "Darwin":
        return subprocess.getoutput(['/usr/sbin/sysctl', "-n", "machdep.cpu.brand_string"]).strip()
    elif platform.system() == "Linux":
        command = "cat /proc/cpuinfo | grep model\\ name"
        return subprocess.getoutput(command).split(": ")[1].split("\n")[0].strip()  # This looks pretty ugly, but it prevents "\nmodel name" appended to the result. Not terribly sure why it's doing that, but under Fedora 26 it does. Don't think it did on my server (TODO) Check output across linuxes


def getRam():
    '''
    http://superuser.com/questions/197059/mac-os-x-sysctl-get-total-and-free-memory-size <--mac
    http://stackoverflow.com/questions/30228366/how-to-find-only-the-total-ram-in-python <--linux
    https://docs.python.org/2/library/string.html
    https://blogs.technet.microsoft.com/askperf/2012/02/17/useful-wmic-queries/ <-- windows

    TODO: consistent memory output? linux outputs it in kB, windows and mac in bytes.
    '''
    if platform.system() == "Windows":
        return subprocess.getoutput(["wmic", "memorychip", "get", "capacity"]).split("\n")[2].strip()
    elif platform.system() == "Darwin":
        return subprocess.getoutput(['/usr/sbin/sysctl', "-n", "hw.memsize"]).strip()  # hw.usermem and others report wrong values supposedly, but hw.memsize works.
    elif platform.system() == "Linux":
        command = "cat /proc/meminfo | grep MemTotal"
        return subprocess.getoutput(command).split(":        ")[1].strip()  # this is bad and could probably be handled better...


def getID():
    '''
    So the idea here is to get a hardware based UUID, we don't want a random one.
    UUID 1 seems to do the trick, however the first part of it changes every time it's generated/read (I think it's time based), so I'm only going to use the last chunk of it.
    That still allows for a pretty good amount of unique machines
    '''
    return(uuid.uuid1().urn.split("-")[4])  # returns something like this: '8c705a21d8fc'


'''
https://docs.python.org/3/howto/logging.html#logging-basic-tutorial
'''

# create logger
l = logging.getLogger('client')
l.setLevel(logging.INFO)

# create file handler and set level to debug
fh = logging.FileHandler('client.log')
fh.setLevel(logging.DEBUG)

# create formatter
fileFormatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter
fh.setFormatter(fileFormatter)

# add to logger
l.addHandler(fh)

l.info("Starting SimpleMon")
l.info("Getting Host Details")

hostDetails = {}
hostDetails["os"] = platform.system() + " " + platform.release()  # "Windows" + " " + "7"
hostDetails["arch"] = platform.architecture()[0]  # we only want 64bits or 32bits
hostDetails["processor"] = getProcessor()
hostDetails["ram"] = getRam()
hostDetails["id"] = getID()  # need a unique identifier for each machine!
hostDetails["hostname"] = platform.node()  # gets the hostname
l.debug(hostDetails)

'''
https://docs.python.org/3/library/ssl.html#ssl.SSLContext
http://stackoverflow.com/questions/19268548/python-ignore-certicate-validation-urllib2
http://www.tornadoweb.org/en/stable/tcpserver.html
https://gist.github.com/weaver/293449
'''
ssl_ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
ssl_ctx.load_cert_chain(os.path.join(os.getcwd(), "server.crt"),
                        os.path.join(os.getcwd(), "server.key"))
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

stuffToSend = b"" + json.dumps(hostDetails).encode() + b"\n"


@gen.coroutine
def send_message():
    stream = yield TCPClient().connect("localhost", 8888, ssl_options=ssl_ctx)
    yield stream.write(stuffToSend)
    l.debug("Sent to server: " + stuffToSend.decode().strip())
    reply = yield stream.read_until(b"\n")
    l.info("Response from server: " + reply.decode().strip())


if __name__ == "__main__":
    IOLoop.current().run_sync(send_message)
