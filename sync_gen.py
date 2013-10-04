# -*- coding: utf-8 -*-
import sync
import sys
import time
import os.path

"""
Python version 3.3.2
Product version 7.3
"""

issue='发布'
ftpRoot='.'
interval=10

def run(once=False):
    global issue,ftpRoot,interval
    try: 
        sync.checkPath([issue]) #检查工作目录存在性
        while True:
            sync.gen(sync.listFiles(issue),os.path.join(ftpRoot,sync.orgFileName),txtAlso=True)
            sync.ImAlive('sync_gen')
            time.sleep(interval)
            if once==True: break
    except Exception as exc: sync.log('System failure',str(exc))

if __name__=='__main__': run()
