# SimpleMon

I'm writing this simple monitoring tool for a school project. If you want to use it, send me an email and I'll put up actual documentation!

`simplemon` aims to be a low setup, cross platform montoring solution.

Features:
 - time series graphs of data
 - alerts via email of downtime
 - written in python for portability/adaptability

Requirements:
 - PostgreSQL server
 - python
 - Mac OS X, Linux 3 or higher, Windows 7 or higher

Generating a cert:
`openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365`
