# -*- coding: utf-8 -*-
#Python version 3.3.2
import py_compile
import os.path
srcs=['sync.py','sync_client.py','sync_gen.py']
omap=[]
for src in srcs:
    filename,ext=os.path.splitext(src)
    omap.append((src,filename+'.pyc'))
for src,out in omap:
    print('compiling',src,'to',out)
    py_compile.compile(src,out)
for src,out in omap:
    fout=open(out,'rb')
    MN=fout.read(2)
    print('magic number of',out,':',end=' ')
    if MN==b'\x9E\x0C':print('9E C [OK]')
    else:print('{0:2X}{1:2X} [Wrong]'.format(MN[0],MN[1]))
    fout.close()
