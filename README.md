# SimpleMon

I'm writing this simple monitoring tool for a school project. If you want to use it, send me an email and I'll put up actual documentation!

`simplemon` aims to be a low setup, cross platform montoring solution.

Requirements:
 - PostgreSQL server
 - python
 - Mac OS X, Linux 3 or higher, Windows 7 or higher
 - OpenSSL (for initial certificate generation)

## Initial setup

#### Database Setup
- Install and configure PostgreSQL.
- Create a user named `simplemon` with the password `simplepass`
    + `CREATE ROLE simplemon UNENCRYPTED PASSWORD 'simplepass' LOGIN;` (as the postgres user)
- Create a database named `simplemon` where the user `simplemon` has owner rights.
    + `CREATE DATABASE simplemon OWNER simplemon;` (as the postgres user)



#### Generating a cert:
Windows users will want to grab OpenSSL from [here.](https://indy.fulgan.com/SSL/openssl-1.0.2k-x64_86-win64.zip)
Linux and Mac OSX users are able to install openssl through their respective package managers.
```bash
openssl req -new -newkey rsa:2048 -days 365 -nodes -x509 -keyout server.key -out server.crt
openssl req -new -newkey rsa:2048 -days 365 -nodes -x509 -keyout client.key -out client.crt
```

#### Running simplemon:
**WARNING: When running simplemon, always make sure the server component is running before running the client component.**

```bash
python server.py
python client.py # most likely in a new window
```

#### To see what's happening in the database:

The easiest way to poke around in the database to see what's going on is a utility called [PgAdmin](https://www.pgadmin.org/).

Install that, configure it to connect to your server, and take a look around in the tables view.
