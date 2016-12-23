import psycopg2      # for database wrangling
import configparser  # for importing configurations for db
import logging       # for logging everything!
'''
https://docs.python.org/3/howto/logging.html#logging-basic-tutorial
'''

# create logger
l = logging.getLogger('client')
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

cur = db.cursor()

try:
    cur.execute("CREATE TABLE nodes (id serial PRIMARY KEY, uuid text, hostname text);")
    db.commit()
    l.debug("Table 'nodes' doesn't exist, creating now")
except:
    l.debug("Table 'nodes' already exists, not creating")
