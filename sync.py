# -*- coding: utf-8 -*-
import os
import time
import datetime
import os.path
import pickle
import sys
import ftplib
import socket
import logging
import logging.handlers
#import win32com.client

"""
Python version 3.3.2
Product version 7.3
"""

def listFiles(tdir):
    """获取tdir路径所指文件夹下文件的列表。数据结构：[(path,[(name,size,time)])]"""
    return [(os.path.relpath(pth,tdir),[(fnn,os.path.getsize(fpp),os.path.getmtime(fpp)) for fnn,fpp in [(fn,os.path.join(pth,fn)) for fn in fs]]) for pth,ds,fs in os.walk(tdir)]
def _cmpf(sf,dfs,ignoreDate):
    """文件比较条件"""
    sn,ss,sd=sf                                                 
    for dn,ds,dd in dfs:
        if sn==dn:
            if ignoreDate:return False
            else:return sd>dd                                    
    else: return True                                               
def compare(lsrc,ldst,ignoreDate=False):
    """比较文件列表lsrc与ldst，返回增量更新列表的迭代器。数据结构：[(path,[(name,size,time)])]"""
    for spth,sfs in lsrc:
        for dpth,dfs in ldst:
            if dpth==spth:
                rfs=[sf for sf in sfs if _cmpf(sf,dfs,ignoreDate)] 
                if len(rfs)>0: yield (spth,rfs)                    
                break
        else: yield (spth,sfs)                                     
def printList(theList,targetFile=sys.stdout):
    """格式化输出文件列表"""   
    for pth,fs in theList:
        print(pth,file=targetFile)
        for n,s,d in fs:
            print('  ',time.strftime("%d %b %Y %H:%M:%S", time.localtime(d)),("%10d"%s),n,file=targetFile)
def setupdir(pth):
    """建立路径中的所有文件夹，返回是否成功"""
    if os.path.exists(pth): return True
    else:
        head,tail=os.path.split(pth)
        if setupdir(head):
            try:
                os.mkdir(pth)
                return True
            except: return False
        else: return False
def nowStr():
    """获取表示当前时间的字符串"""
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

class FatalError(Exception):
    """致命异常，将导致必须放弃一次同步时抛出"""
    def __init__(self,value='Uncertain Error'):
        self.value=str(value)
    def __str__(self):
        return self.value

"""日志对象"""
synclogFileName='sync.log'
synclogger=logging.getLogger('synclogger')
synclogger.setLevel(logging.DEBUG)
syncloggerHandler=logging.handlers.RotatingFileHandler(synclogFileName,maxBytes=6000,backupCount=1)
synclogger.addHandler(syncloggerHandler)

def log(app,msg):
    """记录日志"""
    global synclogger
    #trLog='{0} <{1}> {2}\n'.format(nowStr(),app,msg)
    strLog='{0} <{1}> {2}'.format(nowStr(),app,msg) #yyg20130731
    synclogger.debug(strLog)
    print(strLog)
def getin(FTPInfo):
    """登入FTP"""
    print('FTP INIT')
    host,port,user,password=FTPInfo
    myftp=ftplib.FTP()
    myftp.connect(host,port)
    myftp.login(user,password)
    myftp.encoding='gbk'
    print('FTP Connection <OK>')
    return myftp
def get_my_ip():
    """获取本机活动IP地址"""
    try:
        csock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        csock.connect(('8.8.8.8', 80))
        (addr, port) = csock.getsockname()
        csock.close()
        return addr
    except socket.error:
        return '127.0.0.1'
def download(FTPInfo,fileNames,remotePath='.',storePath='.'):
    """FTP批量下载文件，有错误日志。返回下载失败列表的迭代器。数据结构：[(name,size,time)]"""
    myftp=getin(FTPInfo)
    for fileName,fileSize,fileDate in fileNames:
        fileFullName=os.path.join(storePath,fileName)
        for tries in range(3):
            f=open(fileFullName,'wb')
            try:
                print('FTP RETR <'+fileName+'>')
                myftp.retrbinary('RETR '+os.path.join(remotePath,fileName),f.write,1024)
                break
            except:
                log('download() error','Trying again('+str(tries)+'):'+fileName)
                try:os.remove(fileFullName)
                except:pass
            finally: f.close()
            time.sleep(2)       
        else: yield (fileName,fileSize,fileDate)
        if os.path.getsize(fileFullName)!=fileSize:
            log('download() error','Size does not match:'+fileName)
            try:os.remove(fileFullName)
            except:pass
            yield (fileName,fileSize,fileDate)
    myftp.quit()
def dirx(FTPInfo,remotePath='.'):
    """下载服务器文件列表，有错误日志"""
    myftp=getin(FTPInfo)
    f=open(orgFileName,'wb')
    try:
        print('FTP DIR')
        myftp.retrbinary('RETR '+os.path.join(remotePath,orgFileName),f.write,1024)
    except Exception as exc:
        log('dir() error','Unable to get file list')
        try:os.remove(orgFileName)
        except:pass
        raise FatalError('dir() error') from exc
    finally:
        f.close()
        myftp.quit()
def acknowledge(FTPInfo,remotePath='.',withlog=False):
    """上传回执文件"""
    try:
        strip=get_my_ip()
        fileName=strip.replace('.','_')+'.txt'
        f=open(fileName,'w')
        f.write(strip+' '+nowStr()+'\r\n')
        if withlog:
            try:
                flog=open(synclogFileName)
                f.write('--------------------------------------------------\r\n')   #yyg20130731
                f.write(flog.read())
            except: pass #涉及日志文件本身，不记录日志
        f.close()
        myftp=getin(FTPInfo)
        f=open(fileName,'rb')
        print('FTP ACK')
        myftp.storbinary('STOR '+os.path.join(remotePath,fileName),f,1024)
        f.close()
        myftp.quit()
    except: log('acknowledge() error','Unable to ACK')
    
orgFileName='original.sync'
svrFileName='server.sync'
signEOF='ALXEOF'

def gen(theList,fileName,txtAlso=False):
    """产生文件列表，有错误日志"""
    global signEOF
    signedList=theList[:]
    signedList.append(signEOF)
    try:
        f=open(fileName,'wb') 
        pickle.dump(signedList,f)
        f.close()
        if txtAlso:
            f=open(fileName+'.txt','w')
            printList(theList,f)
            f.close()
    except IOError: pass
    except Exception as exc: log('gen() error',str(exc))
def unserializeList(fileName):
    """文件列表逆序列化，有错误日志"""
    global signEOF
    try:
        f=open(fileName,'rb')
        list1=pickle.load(f)
        f.close()
        if signEOF in list1:
            list1.remove(signEOF)
            return list1
        else:
            return list1
            #下面代码会把可以解析却没有结束标记的文件列表视作无效文件，并引发FatalError
            #log('unserializeList() error','Unsigned list '+fileName)
            #raise FatalError('unserializeList() error')
    except Exception as exc:
        log('unserializeList() error','Cannot unserialize '+fileName)
        try:
            ###
            #os.remove(fileName)
            ###
            rcyc='..\\数据回收'
            rcycName=os.path.join(rcyc,fileName)
            if os.path.exists(rcycName):rcycName=os.path.join(rcyc,getNewName(fn))#避免回收文件重名
            shutil.move(os.path.join('.',fn),rcycName)
            ###
            #log('os.remove',fileName)
            log('exc details',str(exc))
        except: log('os.remove() error',fileName)
        raise FatalError('unserializeList() error') from exc
    
def ImAlive(app):
    """提示程序正在运行"""
    print(app,nowStr(),'alive.')
def getFiles(theList,path):
    """获取某特定路径下的文件列表。实现{[(path,[(name,size,time)])]->[(name,size,time)]}数据结构转换 """
    for pth,fs in theList:
        if pth==path:return fs
    else:return []
def getNewName(fileName):
    """获取新的文件名"""
    filename,ext=os.path.splitext(fileName)
    return filename+datetime.datetime.now().strftime('%Y%m%d%H%M%S')+ext
def checkPath(pths):
    """检查所有文件夹是否都存在，有错误日志"""
    for pth in pths:
        if not os.path.exists(pth):
            log('checkPath() error',pth+'does not exist.')
            raise FatalError('checkPath() error')
    
def check_proc_exsit(process_name):
    WMI = win32com.client.GetObject('winmgmts:')
    processCodeCov = WMI.ExecQuery('select * from Win32_Process where Name="%s"' % process_name)
    if len(processCodeCov) > 0:
        print ('%s is exists' % process_name)
    else:
        print ('%s is not exists' % process_name)
