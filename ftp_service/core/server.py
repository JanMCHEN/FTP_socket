import socketserver
import time
import json
import os
import shutil
from conf.settings import *
import re
from ctypes import *

pid = os.fork()
C_CHAT = CDLL(CFILE)

if pid == 0:
    # python进程异常退出时，此函数可以强制结束此进程
    C_CHAT.prctl(1, 15)
    time.sleep(1)
    print('聊天进程启动...')
    C_CHAT.main()
    exit(0)


def get_size(path, size=0):
    size = size
    file_list = os.listdir(path)
    for file in file_list:
        file = os.path.join(path, file)
        if os.path.isfile(file):
            size += os.stat(file).st_size
        elif os.path.isdir(file):
            size = get_size(file, size)
    return size


class CommandParse(object):

    def __init__(self, path, sock):
        self.home = os.path.abspath(path)
        self.path = self.home
        self.sock = sock
        self.file_size = get_size(self.home)

    def cd(self, data):
        msg = {}
        if len(data) == 1:
            msg['note'] = os.path.relpath(self.path, os.path.dirname(self.home))
        elif len(data) == 2:
            if data[1] == '.':
                self.path = self.home
            elif data[1] == '.' * len(data[1]):
                for _ in range(len(data[1])-1):
                    if self.home == self.path:
                        break
                    self.path = os.path.dirname(os.path.abspath(self.path))
            else:
                msg = self.path_parser(data[1], 1)
        else:
            return {'note': 'cd [path]'}
        msg['dir'] = os.path.relpath(self.path, os.path.dirname(self.home))
        return msg

    def mkdir(self, data):
        if len(data) == 2:
            return self.path_parser(data[1], 2)
        else:
            return {'note': 'mkdir [path]'}

    def ls(self, data):
        msg = {}
        if len(data) == 1:
            msg['note'] = '\n'.join(os.listdir(self.path))
            return msg
        elif len(data) == 2:
            return self.path_parser(data[1], 3)

    def rm(self, data):
        msg = {}
        if len(data) == 2:
            path = os.path.split(data[1])[0]
            if path:
                path = self.path_parser(path).get('dirs')
            else:
                path = self.path
            if path:
                file = os.path.split(data[1])[-1]
                if file:
                    file = os.path.join(path, file)
                    if os.path.isfile(file):
                        self.file_size -= os.stat(file).st_size
                        os.remove(file)
                        msg['note'] = 'done'
                    else:
                        msg['note'] = 'file not found'
                else:
                    self.file_size -= get_size(path)
                    os.rmdir(path)
                    msg['note'] = 'done'
            else:
                msg['note'] = 'path not exist'
        else:
            msg['note'] = 'rm [file]'
        return msg

    def detail(self, data):
        if len(data) == 2:
            file = os.path.join(self.path, data[1])
            if os.path.isfile(file):
                size = os.stat(file).st_size
            elif os.path.isdir(file):
                size = get_size(file)
            else:
                size = 'file not found'
            msg = {'note': str(size)}
        else:
            msg = {'note': 'detail [path]or[file]'}
        return msg

    def upload(self, data, from_others=0):
        dirs = ''
        if len(data) == 1:
            msg = {'note': 'upload [file] [path]'}
            self.sock.sendall(json.dumps(msg).encode("utf8"))
            return
        elif len(data) == 2:
            print('here')
            dirs = self.path
        elif len(data) == 3:
            msg = self.path_parser(data[2])
            dirs = msg.get('dirs')
        if dirs:
            print(dirs)
            msg = {'loop': 'post'}
            self.sock.sendall(json.dumps(msg).encode("utf8"))
            count = json.loads(self.sock.recv(1024).decode('utf8'))['size']
            if self.file_size + count > MAXSIZE:
                self.sock.sendall(b'no')
                return
            self.sock.sendall(b'ok')
            # print(count)
            if count:
                file = os.path.join(dirs, re.split(r'[/\\]', data[1])[-1])
                # print(file)
                if not os.path.isfile(file):
                    self.sock.sendall(b'0')
                    f = open(file, 'wb')
                    received = 0
                    while True:
                        if received < count:
                            data = self.sock.recv(1024)
                            f.write(data)
                            received += len(data)
                        else:
                            break
                    f.close()
                    self.file_size += count
                else:
                    seek = os.path.getsize(file)
                    # print(seek)
                    self.sock.sendall(str(seek).encode("utf8"))
                    f = open(file, 'ab')
                    while True:
                        if seek < count:
                            data = self.sock.recv(1024)
                            f.write(data)
                            seek += len(data)
                        else:
                            break
                    f.close()
                    self.file_size += count-seek
                if from_others:
                    shutil.move(file, os.path.join(self.home, '.temp'))
            else:
                return
        else:
            msg = {'note': 'Path not exist '}
            self.sock.sendall(json.dumps(msg).encode("utf8"))

    def download(self, data, from_others=0):
        dirs = ''
        if len(data) == 1:
            msg = {'note': 'download [file] [path]'}
            self.sock.sendall(json.dumps(msg).encode("utf8"))
            return
        elif len(data) <= 3:
            path = os.path.split(data[1])[0]
            if path:
                msg = self.path_parser(path)
                dirs = msg.get('dirs')
            else:
                dirs = self.path
        else:
            return {'note': 'download [file] [path]'}
        if dirs:
            file = os.path.join(dirs, os.path.split(data[1])[-1])
            if os.path.isfile(file):
                if from_others:
                    return file
                size = os.path.getsize(file)
                msg = {
                    'loop': 'get',
                    'file': os.path.split(data[1])[-1],
                    'size': size
                }
                self.sock.sendall(json.dumps(msg).encode("utf8"))
                seek = self.sock.recv(15).decode('utf8')
                f = open(file, 'rb')
                f.seek(int(seek))
                while True:
                    if size - int(seek):
                        data = f.read(1024)
                        self.sock.sendall(data)
                        size -= len(data)
                    else:
                        break
                f.close()
            else:
                if from_others:
                    return
                return {'note': 'file not exist '}
        else:
            msg = {'note': 'path not found '}
            self.sock.sendall(json.dumps(msg).encode("utf8"))

    def sendto(self, data):
        if len(data) == 3:
            target = os.path.join(os.path.dirname(os.path.abspath(self.home)), data[2])
            if os.path.isdir(target):
                file = self.download(data[:2], 1)
                if file:
                    shutil.copy(file, os.path.join(target, '.temp', os.path.split(file)[-1]))
                    return {'note': 'done'}
                temp = self.path
                self.path = target
                self.upload(data[:2], 1)
                self.path = temp
                return
            else:
                return {'note': 'user not exits'}
        else:
            return {'note': 'sendto [file] [user]'}

    def chatting(self, data):
        print('登入聊天室')
        msg = {'chat': '进入聊天室'}
        self.sock.sendall(json.dumps(msg).encode("utf8"))
        return

    def exit(self, data):
        return {'exit': 1}

    def path_parser(self, path, types=0):

        msg = {}
        if isinstance(path, str):
            path = path.split('/')
            dirs = self.path
            for p in path:
                if p == '.' * len(p):
                    for _ in range(len(p) - 1):
                        if self.home == dirs:
                            break
                        dirs = os.path.dirname(os.path.abspath(dirs))
                else:
                    # print(dirs)
                    dirs = os.path.join(dirs, p)
            if not os.path.exists(dirs):
                if types == 1:
                    msg['note'] = 'Not found the directory'
                elif types == 2:
                    os.makedirs(dirs)
                    msg['note'] = 'done'
                elif types == 3:
                    msg['note'] = "Can't open the directory"
            else:
                if types == 1:
                    self.path = dirs
                elif types == 2:
                    msg['note'] = 'The directory exist'
                elif types == 3:
                    msg['note'] = '\n'.join(os.listdir(dirs))
                elif not types:
                    msg['dirs'] = dirs
        else:
            msg['note'] = 'path_parser is not inside command'
        return msg


class ServerSocket(socketserver.BaseRequestHandler):

    def handle(self):
        print("coon:", self.request)
        print("addr:", type(self.client_address))
        info = self.client_address[0] + ' connect at ' + time.asctime(time.localtime(time.time()))
        self.save(LOGFILE, info+'\n')
        self.times = 0
        while True:
            try:
                data = self.request.recv(1024).strip()
            except (ConnectionResetError, OSError) as e:
                print(e)
                data = ''
            if data:
                data = json.loads(data.decode("utf-8"))
                if hasattr(self, data.get('do')):
                    try:
                        ret = getattr(self, data.get('do'))(**data)
                        if ret == 'ok':
                            self.act(data.get('user'))
                            break
                        elif ret == 'out':
                            print('stop someone')
                            break
                    except TypeError:
                        break
                else:
                    break
            else:
                break
        self.request.close()

    def auth(self, **data):
        data.pop('do')
        msg = ''
        with open(ACCOUNTS, 'r') as f:
            info = f.readlines()
        for acc in info:
            acc_dic = dict(json.loads(acc.strip('\n')))
            if data.get('user') == acc_dic.get('user'):
                if data.get('pwd') == acc_dic.get('pwd'):
                    # self.mode = acc_dic.get('mode')      #用户权力级别
                    msg = 'ok'
                    break
        if not msg:
            msg = 'Authentication failure'
            self.times += 1
        if self.times < RETRY:
            self.request.sendall(msg.encode('utf8'))
        else:
            msg = 'out'
            self.request.sendall(msg.encode('utf8'))
            self.request.close()
        return msg

    def validate(self, **data):
        code = self.request.recv(20).decode('utf8')
        if code == CODE:
            self.request.sendall(b'Y')
        else:
            self.request.sendall(b'N')
            return 'out'

    def sign_up(self, **data):
        data.pop('do')
        with open(ACCOUNTS, 'r') as f:
            info = f.readlines()
        for acc in info:
            acc_dic = dict(json.loads(acc.strip('\n')))
            if data.get('user') == acc_dic.get('user'):
                self.request.sendall(b'The user already exists')
                return
        if len(data.get('user'))<2 or len(data.get('user'))>10:
            self.request.sendall(b'Please confirm that the length of ID you entered matches the standard\
            (at least 2,at most 10)')
            return
        self.save(ACCOUNTS, json.dumps(data)+'\n')
        print("updated")
        self.request.sendall(b'ok')
        return 'ok'

    def save(self, file, info):
        with open(file, "a") as fp:
            fp.writelines(info)

    def act(self, user, mode=0):
        global C_CHAT
        path = USERDIR + '/' + user
        if not os.path.exists(path):
            os.makedirs(path)
            os.makedirs(os.path.join(path, '.temp'))
        CP = CommandParse(path, self.request)
        while True:
            try:
                data = self.request.recv(1024)
            except (ConnectionResetError, OSError) as e:
                # print(e)
                data = ''
            msg = {}
            if data:
                data = data.decode("utf-8").split()
                if hasattr(CommandParse, data[0]):
                    msg = getattr(CommandParse, data[0])(CP, data)
                else:
                    msg['note'] = "{} not the inside command".format(data[0])
                # print(msg)
                if msg:
                    self.request.sendall(json.dumps(msg).encode("utf8"))
                    if msg.get('exit'):
                        print('{} out'.format(user))
                        self.request.close()
                        break
            else:
                break
