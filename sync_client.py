# -*- coding: utf-8 -*-
import os
import os.path
import shutil
import sync
import time
import subprocess

"""
Python version 3.3.2
Product version 7.3

列表结构标注 '^'~[(path,[(name,size,time)])],''~[(name,size,time)],'_'~[name],'_,_'~[(src,dst)].
"""

store='数据接收\\DAT'
rcyc='数据回收'
issue='发布'
disRoot='数据显示'
display='数据显示\\ShowData'
myftp='192.168.1.13',21,'FTP用户名','FTP密码'
proc='display.exe'
ackpth='.'
interval=15

def recycle(removals):
    """回收过期文件"""
    global store,rcyc
    for fn,fs,fd in removals:
        try:
            rcycName=os.path.join(rcyc,fn)
            if os.path.exists(rcycName):rcycName=os.path.join(rcyc,sync.getNewName(fn)) #避免回收文件重名
            shutil.move(os.path.join(store,fn),rcycName)
        except: sync.log('recycle() error','From '+os.path.join(store,fn)+' to '+rcycName)

def refreshDisplay():
    """更新实际显示文件"""
    global store,disRoot,display,proc
    displayWasAlive=(os.system('taskkill /F /IM '+os.path.basename(proc))==0)       #终止display进程
    time.sleep(1)
    try:
        spefs=[('Message.txt','show.txt'),('data.zdb','data.zdb')]                  #display系统文件表_,_
        for sffsrc,sffdst in spefs: shutil.copy(os.path.join(store,sffsrc),os.path.join(disRoot,sffdst)) #复制display系统文件
        dis=sync.listFiles(display)                                                 #显示表^
        sto=sync.listFiles(store)                                                   #本地表^
        for ffn,ffs,ffd in sync.getFiles(sync.compare(dis,sto,ignoreDate=True),'.'):#删除过期文件
            try: os.remove(os.path.join(display,ffn))
            except: pass
        sfsrcs=[src for src,dst in spefs]
        for ffn,ffs,ffd in sync.getFiles(sync.compare(sto,dis),'.'):                #复制新增文件（除了display系统文件以外）
            if ffn not in sfsrcs: shutil.copy(os.path.join(store,ffn),os.path.join(display,ffn))
        sync.log('refreshDisplay()','Success to sync between "store" and "display"')    #yyg20130731
    except: sync.log('refreshDisplay() error','Fail to sync between "store" and "display"')
    time.sleep(1)
    if displayWasAlive: subprocess.Popen(proc)                                      #启动display进程

def getTargets(svr,sto):
    """计算下载目标"""
    try:
        svr_=sync.unserializeList(sync.svrFileName)         #备份表^
        upd1=sync.compare(svr,svr_)                         #更新表^
    except sync.FatalError:                                 #捕获逆序列化失败造成的FatalError，采用备用更新表
        _upd1=['Message.txt','data.zdb','外汇牌价.jpg','UpDate.ini']      #备用更新表_   #yyg20130731
        upd1=[('.',[(ffn,ffs,ffd) for ffn,ffs,ffd in sync.getFiles(svr,'.') if ffn in _upd1])]
    upd2=sync.compare(svr,sto)                              #新增表^
    exclusions=['Thumbs.db']                                #排除表_
    targets1=[(ffn,ffs,ffd) for ffn,ffs,ffd in sync.getFiles(upd1,'.') if ffn not in exclusions]
    targets2=[(ffn,ffs,ffd) for ffn,ffs,ffd in sync.getFiles(upd2,'.') if ffn not in exclusions]
    targets=targets1[:];t1ffns=[ffn for ffn,ffs,ffd in targets1];targets.extend([(ffn,ffs,ffd) for ffn,ffs,ffd in targets2 if ffn not in t1ffns])
    return targets # = targets1（更新表） ∪ targets2（新增表）

def download(targets):
    """下载所有目标"""
    global myftp,issue,store
    fails=sync.download(myftp,targets,remotePath=issue,storePath=store) 
    return [i for i in fails]

def run(once=False):
    global store,rcyc,disRoot,display,myftp,ackpth,interval
    try:
        sync.checkPath([store,rcyc,disRoot,display,r'C:\Windows\System32\taskkill.exe']) #检查工作目录存在性
        while True:
            try: 
                sync.dirx(myftp)                            #下载服务器文件表        
                svr=sync.unserializeList(sync.orgFileName)  #服务器文件表^
                #############   关键变更，测试正确后删除注释   #############
                #try:
                #    svr_=sync.unserializeList(sync.svrFileName)#备份表^
                #    upd1=sync.compare(svr,svr_)             #更新表^
                #except sync.FatalError:
                #    upd1=[('.',[''])]
                #sto=sync.listFiles(store)                   #本地表^
                #upd2=sync.compare(svr,sto)                  #新增表^
                #changes=0                                   #清空文件变更数
                #exclusions=['Thumbs.db']                    #排除表_
                #targets1=[(ffn,ffs,ffd) for ffn,ffs,ffd in sync.getFiles(upd1,'.') if ffn not in exclusions]
                #t1ffns=[ffn for ffn,ffs,ffd in targets1]
                #targets2=[(ffn,ffs,ffd) for ffn,ffs,ffd in sync.getFiles(upd2,'.') if ffn not in exclusions]
                #targets=targets1[:];targets.extend([(ffn,ffs,ffd) for ffn,ffs,ffd in targets2 if ffn not in t1ffns])#计算确认下载文件列表
                #########################################################
                sto=sync.listFiles(store)                   #本地表^
                changes=0                                   #清空文件变更数
                targets=getTargets(svr,sto)
                #########################################################
                changes+=len(targets)                       #记录下载文件数
                print('len(targets):',len(targets));print('targets:',targets)               
                rms=sync.getFiles(sync.compare(sto,svr,ignoreDate=True),'.') #回收表
                changes+=len(rms)                           #记录移除文件数
                recycle(rms)                                #回收过期文件
                fails=download(targets)                     #下载文件并获取失败表
                shutil.copy(sync.orgFileName,sync.svrFileName)#另存服务器文件表
                if changes: refreshDisplay()
                sync.acknowledge(myftp,ackpth,withlog=True) #提交回执（和日志）
                sync.ImAlive('sync_client')              
                time.sleep(interval)
            except: time.sleep(10)                          #致命异常导致10秒后开始新循环
            if once==True:break
    except Exception as exc: sync.log('System failure',str(exc))

if __name__=='__main__': run()
