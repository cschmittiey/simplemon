import psycopg2      # for database wrangling
import configparser  # for importing configurations for db
import logging       # for logging everything!
import sys           # for exiting
import json          # for sending stuff over the network
from tornado.tcpserver import TCPServer
from tornado.iostream import StreamClosedError
from tornado import gen
import tornado
import ssl
import os
import datetime
from apscheduler.schedulers.tornado import TornadoScheduler   # for multiprocess CPU and RAM utilization grabbing
import requests
import paramiko

'''
https://docs.python.org/3/howto/logging.html#logging-basic-tutorial
'''

# create logger
l = logging.getLogger('server')
l.setLevel(logging.INFO)

# create file handler and set level to debug
fh = logging.FileHandler('server.log')
fh.setLevel(logging.DEBUG)

# create formatter
fileFormatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter
fh.setFormatter(fileFormatter)

# add to logger
l.addHandler(fh)

l.debug("Reading Config")
config = configparser.ConfigParser()
config.read('server.config.ini')
'''
https://wiki.postgresql.org/wiki/Psycopg2_Tutorial
'''
try:
    db = psycopg2.connect("dbname={0} user={1} password={2} host={3} port={4}".format(config['database']['dbname'],
                                                                                      config['database']['dbusername'],
                                                                                      config['database']['dbpassword'],
                                                                                      config['database']['dbhost'],
                                                                                      config['database']['dbport']))
except:
    l.fatal("Can't connect to the database. Check your config, that postgres is running, and that you have access to the database.")
    sys.exit(1)

cur = db.cursor()


def insertNode(uuid, hostname):
    '''
    http://initd.org/psycopg/docs/usage.html
    '''
    if (isinstance(uuid, str) and isinstance(hostname, str)):
        cur.execute("INSERT INTO nodes (id, uuid, hostname) VALUES (DEFAULT, %s, %s)", (uuid, hostname))
        db.commit()


def insertService(node, serviceType, ipAddress, username, password):
    '''
    http://initd.org/psycopg/docs/usage.html
    '''
    if (isinstance(node, str) and isinstance(serviceType, str) and isinstance(ipAddress, str) and isinstance(username, str) and isinstance(password, str)):
        cur.execute("INSERT INTO services (id, node_id, type, ipAddress, username, password) VALUES (DEFAULT, %s, %s, %s, %s, %s)", (node, serviceType, ipAddress, username, password))
        db.commit()


def insertMeasurement(table, node, time, measurement):
    if table == 'ram':
        if node in newNodeList:
            cur.execute("INSERT INTO ram (id, node_id, measurementTime, percentage) VALUES (DEFAULT, %s, %s, %s)", (node, time, measurement))
            db.commit()
        else:
            l.warn("Someone's trying to insert data for a node that doesn't exist.")
            l.warn(table + " " + node + " " + time + " " + measurement)
    elif table == 'cpu':
        if node in newNodeList:
            cur.execute("INSERT INTO cpu (id, node_id, measurementTime, percentage) VALUES (DEFAULT, %s, %s, %s)", (node, time, measurement))
            db.commit
        else:
            l.warn("Someone's trying to insert data for a node that doesn't exist.")
            l.warn(table + " " + node + " " + time + " " + measurement)
    elif table == 'servicemeasurements':
        if node in newNodeList:
            cur.execute("INSERT INTO servicemeasurements (id, node_id, measurementTime, upOrDown) VALUES (DEFAULT, %s, %s, %s)", (node, time, measurement))
            db.commit
        else:
            l.warn("Someone's trying to insert data for a node that doesn't exist.")
            l.warn(table + " " + node + " " + time + " " + measurement)

    else:
        l.warn("Somone's trying to insert data into a table that doesn't exist.")
        l.warn(table + " " + node + " " + time + " " + str(measurement))
        l.warn(type(table))


def createTable(arg, carefullyFormattedSqlVariables):
    '''
    http://initd.org/psycopg/docs/usage.html#passing-parameters-to-sql-queries
    Generally, we should not use string concatenation/formatting to pass things into psycopg2.
    however, this is an exception to the rule, because it is the name of a table, not data being inserted into the db.
    '''
    sql = "CREATE TABLE {} {};".format(arg, carefullyFormattedSqlVariables)
    try:
        cur.execute(sql)
        db.commit()
        l.info("Table '{}' doesn't exist, creating now".format(arg))
    except:
        l.info("Either Table '{}' already exists, or something else went wrong.".format(arg))
        db.rollback()


createTable("nodes", "(id serial PRIMARY KEY, uuid text UNIQUE, hostname text)")
createTable("services", "(id serial PRIMARY KEY, node_id text REFERENCES nodes (uuid) ON DELETE CASCADE, type text, ipAddress text, username text, password text)")
createTable("ram", "(id serial PRIMARY KEY, node_id text REFERENCES nodes (uuid) ON DELETE CASCADE, measurementTime timestamp, percentage real)")
createTable("cpu", "(id serial PRIMARY KEY, node_id text REFERENCES nodes (uuid) ON DELETE CASCADE, measurementTime timestamp, percentage real)")
createTable("servicemeasurements", "(id serial PRIMARY KEY, node_id text REFERENCES nodes (uuid) ON DELETE CASCADE, measurementTime timestamp, upOrDown boolean)")

'''
I should get a list of nodes already so we don't add a duplicate one below.
'''

cur.execute("SELECT uuid FROM nodes;")
nodeList = cur.fetchall()

newNodeList = []
for element in nodeList:
    newNodeList.append(element[0])

'''
Here comes the networking! Now that we've got it talking to the database, and logging,
we're ready to network with client applications and recieve time-series data and node info.


https://docs.python.org/3/library/ssl.html#ssl.SSLContext
http://stackoverflow.com/questions/19268548/python-ignore-certicate-validation-urllib2
http://www.tornadoweb.org/en/stable/tcpserver.html
https://gist.github.com/weaver/293449

'''


def processHostDetails(data):
    '''
    Data comes in from the server stream, as bytes, representing a json dict.
    We want to avoid adding duplicate nodes, so each node calculates a UUID based on it's hardware,
    and transmits it with it's hostDetails, so that we can avoid duplicate DB entries.
    '''
    hostDetails = json.loads(data.decode().strip())
    l.info("Received host details for node " + hostDetails['id'] + " " + hostDetails['hostname'])
    if hostDetails['id'] in newNodeList:
        return(b"Node is already registered\n")
        l.info("Node is already registered")
    else:
        insertNode(hostDetails['id'], hostDetails['hostname'])
        newNodeList.append(hostDetails['id'])
        l.info("Node " + hostDetails['id'] + " " + hostDetails['hostname'] + " added")
        return(b"Node " + hostDetails['id'].encode() + b" " + hostDetails['hostname'].encode() + b" added")


def processRam(data):
    '''
    Gotta get the json+bytes string back to a database with a datetime timestamp,
    and then add the data point to the database.
    This should be very similar to processHostDetails().
    '''
    usedRam = json.loads(data.decode().strip())
    insertMeasurement("ram", usedRam['id'], usedRam['timestamp'], usedRam['usedRam'])
    return(b'Measurement Added\n')


def processCpu(data):
    '''
    Gotta get the json+bytes string back to a database with a datetime timestamp,
    and then add the data point to the database.
    This should be very similar to processHostDetails().
    '''
    usedCpu = json.loads(data.decode().strip())
    insertMeasurement("cpu", usedCpu['id'], usedCpu['timestamp'], usedCpu['usedCpu'])
    return(b'Measurement Added\n')


def processService(data):
    '''
    let's insert a service!
    '''
    if data[1].decode()[0] == '{':
        response = json.loads(data[1].decode().strip())
    else:
        response = data[1].decode().strip()
    if isinstance(response, dict):
        insertService(response['id'], response['serviceType'], response['ipAddress'], response['username'], response['password'])
    else:
        l.info("Recieved a service#no")
    return(b"Service information Processed\n")


def checkServices():
    '''
    For checking SSH services, we'll use the paramiko library.
    http://jessenoller.com/blog/2009/02/05/ssh-programming-with-paramiko-completely-different

    For checking HTTP services, we'll use the requests library.
    http://stackoverflow.com/questions/1140661/what-s-the-best-way-to-get-an-http-response-code-from-a-url

    format of incoming query results:
    (id, node_id, serviceType, ipAddress, username, password)
    (1, '8c705a21d8fc', 'http', '127.0.0.1', '', '')
    '''
    cur.execute("SELECT * FROM services")
    services = cur.fetchall()
    for service in services:
        if service[2] == 'http':
            try:
                r = requests.head("http://" + service[3])
                insertMeasurement("servicemeasurements", service[1], datetime.datetime.now(), True)
            except requests.ConnectionError:
                insertMeasurement("servicemeasurements", service[1], datetime.datetime.now(), False)
        elif service[2] == 'ssh':
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                ssh.connect(service[3], username=service[4], password=service[5])
                insertMeasurement("servicemeasurements", service[1], datetime.datetime.now(), True)
            except NoValidConnectionsError:
                insertMeasurement("servicemeasurements", service[1], datetime.datetime.now(), False)
        else:
            l.warn("Someone's trying to monitor a service that we don't know how to monitor.")


ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
ssl_ctx.load_cert_chain(os.path.join(os.getcwd(), "server.crt"),
                        os.path.join(os.getcwd(), "server.key"))


class EchoServer(TCPServer):
    @gen.coroutine
    def handle_stream(self, stream, address):
        while True:
            try:
                data = yield stream.read_until(b"\n")
                l.debug("Received bytes: %s", data)
                data = data.split(b"#")
                if data[0] == b"hostDetails":
                    yield stream.write(processHostDetails(data[1]))
                elif data[0] == b"ram":
                    yield stream.write(processRam(data[1]))
                    l.info("RAM measurement recieved")
                elif data[0] == b"cpu":
                    yield stream.write(processCpu(data[1]))
                    l.info("CPU measurement recieved")
                elif data[0] == b"service":
                    yield stream.write(processService(data))  # We're passing the entirety of `data` here because the function should detect whether we recieve service#no or service#{array of information}
                    l.info("Service information processed")
                else:
                    yield stream.write(b"ok\n")
            except StreamClosedError:
                l.debug("Lost client at host %s", address[0])
                break
            except Exception as e:
                print(e)


print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))
server = EchoServer(ssl_options=ssl_ctx)
server.listen(8888)

sched = TornadoScheduler()
sched.add_job(checkServices, 'interval', seconds=10)

sched.start()

tornado.ioloop.IOLoop.current().start()

# Make the changes to the database persistent
db.commit()

# Close communication with the database
cur.close()
db.close()
