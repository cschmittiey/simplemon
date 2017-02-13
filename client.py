import platform     # Platform data, such as OS type, release, etc
import subprocess   # Used for running local console commands
import sys          # Used to determine system python version, as we need Python 3 and not 2
import logging      # Well, it's used for logging. Importing it as l because I'm lazy and don't want to type logging everytime.
import uuid         # to distinguish hosts
from tornado.ioloop import IOLoop  # all the tornado stuff is networking
from tornado import gen
from tornado.tcpclient import TCPClient
import ssl          # for encrypted networking
import os           # useful for finding current directory across OSes.
import json         # for encoding network traffic in a sane format
from apscheduler.schedulers.tornado import TornadoScheduler   # for multiprocess CPU and RAM utilization grabbing
import psutil       # for getting RAM usage
import datetime     # for timestamps
import ipaddress    # for validation of ipadresses
import configparser  # for config parsing

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

config = configparser.ConfigParser()
config.read('client.config.ini')


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


def getUsedRam():
    '''
    http://stackoverflow.com/questions/3393612/run-certain-code-every-n-seconds
    http://stackoverflow.com/questions/276052/how-to-get-current-cpu-and-ram-usage-in-python
    '''
    l.info("Getting used RAM")
    memory = psutil.virtual_memory()
    temp = {}
    temp['usedRam'] = memory.percent
    temp['id'] = getID()
    temp['timestamp'] = datetime.datetime.now().isoformat()
    return temp
    l.info(temp)


def getUsedCpu():
    '''
    http://stackoverflow.com/questions/3393612/run-certain-code-every-n-seconds
    http://stackoverflow.com/questions/276052/how-to-get-current-cpu-and-ram-usage-in-python
    '''
    l.info("Getting used CPU")
    cpu = psutil.cpu_percent()
    temp = {}
    temp['usedCpu'] = cpu
    temp['id'] = getID()
    temp['timestamp'] = datetime.datetime.now().isoformat()
    return temp
    l.info(temp)


def getServiceDetails():
    if config['client']['serviceAlreadyConfigured'] == "no":
        if input("Would you like to configure uptime monitoring of SSH or HTTP services? [y/n] ").startswith("y"):
            success = False
            tries = 0
            while tries < 5 and success is not True:
                ipAddress = input("Please enter the IP Address the service listens on: ")
                try:
                    if ipaddress.ip_address(ipAddress):
                        success = True
                except ValueError:
                    print("Sorry, that doesn't seem to be a proper IP Address. ")
                    success = False
                tries = tries + 1
            serviceType = input("SSH or HTTP? [ssh/http/cancel] ")
            if serviceType.startswith("s"):
                serviceType = "ssh"
                username = input("Please enter the username to use when connecting: ")
                password = input("Please enter the password to use when connecting: ")
            elif serviceType.startswith("h"):
                serviceType = "http"
                username = ""
                password = ""
            else:
                print("Cancelling")
                return(b"no")
            tempArray = {}
            tempArray["serviceType"] = serviceType
            tempArray["ipAddress"] = ipAddress
            tempArray["id"] = getID()
            tempArray["username"] = username
            tempArray["password"] = password
            config['client']['serviceAlreadyConfigured'] = 'yes'
            cfgfile = open('client.config.ini', 'w')
            config.write(cfgfile)
            return(json.dumps(tempArray).encode())
        else:
            return(b"no")
    else:
        return(b"no")


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
ssl_ctx.load_cert_chain(os.path.join(os.getcwd(), "client.crt"),
                        os.path.join(os.getcwd(), "client.key"))
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE


@gen.coroutine
def send_message(stuffToSend):
    stream = yield TCPClient().connect("localhost", 8888, ssl_options=ssl_ctx)
    yield stream.write(stuffToSend)
    l.debug("Sent to server: " + stuffToSend.decode().strip())
    reply = yield stream.read_until(b"\n")
    l.info("Response from server: " + reply.decode().strip())


sched = TornadoScheduler()


if __name__ == "__main__":
    '''
    http://stackoverflow.com/questions/3393612/run-certain-code-every-n-seconds
    '''
    send_message(b"hostDetails#" + json.dumps(hostDetails).encode() + b"\n")  # send off the host details.
    send_message(b"service#" + getServiceDetails() + b"\n")
    sched.add_job(lambda: send_message(b"ram#" + json.dumps(getUsedRam()).encode() + b"\n"), 'interval', seconds=10)  # creates a scheduler to send a measurement every 10 seconds.
    sched.add_job(lambda: send_message(b"cpu#" + json.dumps(getUsedCpu()).encode() + b"\n"), 'interval', seconds=10)
    sched.start()
    print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))
    try:
        IOLoop.instance().start()
    except (KeyboardInterrupt, SystemExit):
        pass
