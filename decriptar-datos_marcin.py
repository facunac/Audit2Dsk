#!/usr/bin/env python

import sys
import MySQLdb as db
import MySQLdb.cursors
from Crypto.Cipher import AES
import struct
from cStringIO import StringIO

def get_pt_key():
    data_key = bytearray("hu.gor-74-a\\\xD1\xE7)d0ew3@(\t#\"_^ja'& ")
    data_key[9]  = '+'
    data_key[20] = '6'
    data_key[25] = 'j'
    return str(data_key)

def get_au_key():
    data_key = bytearray("hu.gor-74-a\\\xEF\xBF\xBD)d0ew3@(\t#\"_^ja'& ")
    data_key[9]  = '+'
    data_key[20] = '6'
    data_key[25] = 'j'
    return str(data_key)

def aes_create_key(key):
    real_key = bytearray(32)
    n = 0
    for c in key:
	if n == 32: n = 0
	real_key[n] ^= ord(c)
	n += 1
    return str(real_key)

def aes_decode(data, key):
    key = aes_create_key(key)
    aes = AES.new(key)
    padded = aes.decrypt(data)
    padding_size = ord(padded[-1])
    if padding_size > 16:
	raise Exception("decryption failure")
    return padded[:-padding_size]

def sec_decrypt(data):
    decoded = bytearray(aes_decode(data, get_pt_key()))
    decoded[211] = 0xff - decoded[211]
    decoded[259] = 0xff - decoded[259]
    return str(decoded)

def get_rut_key(rut, opt):
    rut = bytearray(rut)
    key = None
    if (rut[9] - ord('0') + opt) % 2 == 0:
	key = bytearray("hu.Zor+74-&\\\xD1\xE7ld0ew>@(\t#\"_^ja'&1")
    else:
	key = bytearray("m3wZ55*\\4^jd/\"ld\t0'&e\xD1\xE7w>@(#\"_a")
    # intercambiamos un par de bytes
    i = rut[8] - ord('0')
    j = rut[6] - ord('0')
    c = key[i]
    key[i] = key[j]
    key[j] = c
    # ponemos algunos cc del Rut en la Key
    key[rut[7] - ord('0')] = rut[5]
    key[rut[5] - ord('0')] = rut[4]
    key[rut[9] - ord('0')] = 0
    key[opt] = rut[11]
    return str(key)

def pri_decrypt(data, rut, opt):
    key = get_rut_key(rut, opt)
    return aes_decode(data, key)

def dec64(e):
    e = e + "=" * (4 - (len(e) % 4))
    e = e.decode('base64')
    return e

def unpack_tdedos(row):
    tmp = dec64(row['Institucion'])
    row['Institucion'] = pri_decrypt(tmp, row['RUT'], 1)
    tmp = dec64(row['Datos'])
    row['Datos'] = pri_decrypt(tmp, row['RUT'], 2)
    datos = row['Datos']
    campos = datos.split('\x00', 3)
    row['TipoEnrola'] = campos[0]
    row['Estacion'] = campos[1]
    row['RutOper'] = campos[2]
    (length, ) = struct.unpack('<i', campos[3][1:5])
    print row
    return
    row['Patron'] = campos[3][5:5+length]
    row['TieneWSQ'] = campos[3][5+length:5+length+1]
    row['Patron'] = sec_decrypt(row['Patron'])
    del row['Datos']

LRUT=12
def pseudo_rut(s):
    r = [0] * 12
    n = len (s)
    for i in range(LRUT):
	c = ord(s[i % n])
	if c >= ord('A') and c <= ord('Z'):
	    c = c - ord('A') + ord('a')
	r[i] = (c % 10) + ord('0')
    r[10] = ord('-')
    return "".join(map(chr, r))

def unpack_tinstitucion(row):
    tmp = dec64(row['Datos'])
    row['Datos'] = pri_decrypt(tmp, pseudo_rut(row['id']), 2)
    datos = row['Datos']
    print 'DECRYPTED', repr(datos)
    # campos = datos.split('\x00', 3)
    # print campos

def unpack_tpersonas(row):
    tmp = dec64(row['Institucion'])
    row['Institucion'] = pri_decrypt(tmp, row['RUT'], 0)
    tmp = dec64(row['Datos'])
    row['Datos'] = pri_decrypt(tmp, row['RUT'], 2)
    datos = row['Datos']
    print 'DECRYPTED', repr(datos)
    # campos = datos.split('\x00', 3)
    # print campos

def pseudo_rut_2(s):
    r = [0] * 14
    s = [ord(c) for c in s]
    r[0:4] = s[15:19]
    r[4:8] = s[10:14]
    r[8:10]= s[5 :7]
    r[10] = ord('-')
    r[11] = (s[18] % 10) + ord('0')
    r[12] = 0
    r[4]  = s[7]
    for i in range(LRUT):
	r[i] = (r[i] % 10) + ord('0')
    r = r[0:12]
    return "".join(map(chr, r))

def unpack_taudit(row):
    tmp = row['Datos']
    try:
	row['Datos'] = pri_decrypt(tmp, pseudo_rut_2(row['NroAudit']), 3)
	datos = row['Datos']
	print 'DECRYPTED:', repr(datos)
    except:
	print 'UNDECRYPTED:', repr(tmp)

cn = db.connect(host = "127.0.0.1", user = "autentia", passwd = '_voyager.', port=3306,
                db = "autentia" )
cr = cn.cursor()

for rut in sys.argv[1:]:
    rut = rut.rjust(12, '0').upper()
    cr.execute("SELECT * FROM TDedos WHERE Pais = 'CHILE' AND RUT = %s AND Vigente = 'S'", (rut, ))
    n = 1
    rows = cr.fetchall()
    if rows:
	for row in rows:
	    unpack_tdedos(row)
	    print row
	    # patron = row['Patron']
	    # iddedo = row['Dedo']
	    # print "%02d %s %d" % (n, rut, iddedo)
	    # open('patrones/%s-%02d-%02d.dat' % (rut, n, iddedo), 'wb').write(patron)
	    n += 1
    else:
	print "%s sin registros." % rut

cr.execute("SELECT NroAudit,Datos,Registrado FROM TAudit WHERE Datos not like 's3%' order by registrado desc limit 5")
LABELS=("NroAudit","Datos","Registrado")

MAXROWS = 250
rows = cr.fetchmany(size = MAXROWS)
while rows:
    for row in rows:
	row =  dict(zip(LABELS,row))
        unpack_taudit(row)
	print row
    rows = cr.fetchmany(size = MAXROWS)

# cr.execute("SELECT * FROM TInstitucion LIMIT 10")
# for row in cr.fetchall():
#     print row
#     unpack_tinstitucion(row)
#     print row

# cr.execute("SELECT * FROM TPersonas WHERE RUT != '' LIMIT 10")
# for row in cr.fetchall():
#     unpack_tpersonas(row)
#     print row

cr.close()
cn.close()
