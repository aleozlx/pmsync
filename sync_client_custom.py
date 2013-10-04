# -*- coding: utf-8 -*-
#Python version 3.3.2
import sync_client
sync_client.store='..\\数据接收\\DAT'
sync_client.rcyc='..\\数据回收'
sync_client.disRoot='..\\数据显示'
sync_client.display='..\\数据显示\\ShowData'
sync_client.issue='DAT'
sync_client.myftp='192.168.1.14',21,'FTP用户名','FTP密码'
sync_client.interval=20
sync_client.proc='..\\数据显示\\display.exe'
sync_client.ackpth='回执'
sync_client.run()
