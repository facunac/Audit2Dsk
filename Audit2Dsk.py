#!/usr/bin/python

import sys
import os
from datetime import datetime
import MySQLdb
import pickle
from optparse import OptionParser

parser = OptionParser()
parser.add_option("-u", "--user", dest="pDBuser", help="Usuario base de datos", default="autentia")
parser.add_option("-p", "--password", dest="pDBpass", help="Password base de datos", default="")
parser.add_option("-s", "--server", dest="pDBhost", help="Host base de datos", default="base.autentia.cl")
parser.add_option("-d", "--database", dest="pDBname", help="Nombre base de datos", default="autentia")
parser.add_option("-c", "--cantidad", dest="pDBcant", help="Cantidad de registros", default=100,type="int")
parser.add_option("-z", "--home", dest="pPath", help="Carpeta donde dejara los archivos", default="/home/PKL", type = "string")
parser.add_option("-b", "--bucket", dest="pBucket", help="Bucket en Amazon S3", default="autentia-audit", type = "string")

(options, args) = parser.parse_args()

if not options.pDBpass:
	parser.error('la password de la base de datos es obligatoria. (-p|--password)')

pHome = options.pPath
if pHome[-1] != "/":
	pHome += "/"

db = MySQLdb.connect(options.pDBhost, options.pDBuser, options.pDBpass, options.pDBname)

cursor = db.cursor()

sql = "select * from TAudit where server <> 'AMAZONS3' order by registrado limit %d" % (options.pDBcant)
#try:
cursor.execute(sql)
results = cursor.fetchall()
for row in results:
	nAudit = ""
	nAudit = row[0]
	dRegistrado = row[2]
	print str(dRegistrado)
	pPath = pHome + nAudit[0:4] + "/" + str(dRegistrado)[0:4] + "/" + str(dRegistrado)[5:7] + "/" + str(dRegistrado)[8:10] + "/" + row[0] + ".pkl"
	print os.path.dirname(pPath)

	if not os.path.exists(os.path.dirname(pPath)):
		os.makedirs(os.path.dirname(pPath))

	print pPath
	output = open(pPath, 'wb')
	pickle.dump(row, output)
	output.close()
#except:
#	print "Error: unable to fecth data"

db.close()
