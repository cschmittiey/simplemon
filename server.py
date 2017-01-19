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

'''
https://docs.python.org/3/howto/logging.html#logging-basic-tutorial
'''

# create logger
l = logging.getLogger('server')
l.setLevel(logging.DEBUG)

# create console handler and set level to info -- we don't want console spam.
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# create file handler and set level to debug
fh = logging.FileHandler('server.log')
fh.setLevel(logging.DEBUG)

# create formatters
fileFormatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamFormatter = logging.Formatter('%(levelname)s - %(message)s')

# add formatter
ch.setFormatter(streamFormatter)
fh.setFormatter(fileFormatter)

# add to logger
l.addHandler(ch)
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


def insertService(node, type):
    '''
    http://initd.org/psycopg/docs/usage.html
    '''
    if (isinstance(node, int) and isinstance(type, str)):
        cur.execute("INSERT INTO services (id, node_id, type) VALUES (DEFAULT, %s, %s)", (node, type))
        db.commit()


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
        l.debug("Table '{}' doesn't exist, creating now".format(arg))
    except:
        l.debug("Either Table '{}' already exists, or something else went wrong.".format(arg))
        db.rollback()

createTable("nodes", "(id serial PRIMARY KEY, uuid text, hostname text)")
createTable("services", "(id serial PRIMARY KEY, node_id int REFERENCES nodes (id) ON DELETE CASCADE, type text)")


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
    '''
    hostDetails = json.loads(data.decode().strip())
    l.debug("Received host details for node " + hostDetails['id'] + " " + hostDetails['hostname'])
    if hostDetails['id'] in newNodeList:
        return(b"Node is already registered\n")
        l.info("Node is already registered")
    else:
        insertNode(hostDetails['id'], hostDetails['hostname'])
        newNodeList.append(hostDetails['id'])
        l.info("Node" + hostDetails['id'] + " " + hostDetails['hostname'] + " added")
        return(b"Node added\n")

ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
ssl_ctx.load_cert_chain(os.path.join(os.getcwd(), "server.crt"),
                        os.path.join(os.getcwd(), "server.key"))


class EchoServer(TCPServer):
    @gen.coroutine
    def handle_stream(self, stream, address):
        while True:
            try:
                data = yield stream.read_until(b"\n")
                print("Received bytes: %s", data)
                if data.startswith(b"{"):
                    yield stream.write(processHostDetails(data))
                if not data.endswith(b"\n"):
                    data = data + b"\n"
                yield stream.write(data)
            except StreamClosedError:
                print("Lost client at host %s", address[0])
                break
            except Exception as e:
                print(e)

server = EchoServer(ssl_options=ssl_ctx)
server.listen(8888)
tornado.ioloop.IOLoop.current().start()

# Make the changes to the database persistent
db.commit()

# Close communication with the database
cur.close()
db.close()
