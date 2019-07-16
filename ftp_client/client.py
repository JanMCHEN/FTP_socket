from socket import *
import optparse,json
import os
from ctypes import *


# 解析c文件，即初始化聊天程序
C_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'client.so')
C_CHAT = CDLL(C_FILE)


class ClientSocket():
    def __init__(self):
        self.sock = socket(AF_INET, SOCK_STREAM)
        op = optparse.OptionParser()
        op.add_option("-i", "--ip_addr", dest="ip_addr")
        op.add_option("-P", "--port", dest="port")
        op.add_option("-u", "--username", dest="username")
        op.add_option("-p", "--password", dest="password")
        options, args = op.parse_args()
        # 程序入口
        self.verify_args(options, args)

    def verify_args(self, opt, args):
        # 对程序启动时传入的参数作解析
        if args and args[0] == 'help':
            self.help()
            return
        if not opt.ip_addr:
            opt.ip_addr = "127.0.0.1"
        if not opt.port:
            opt.port = 8880
        self.sock.connect((opt.ip_addr, int(opt.port)))
        if not opt.username:
            ch = input("SignIn or SignUp[I/U]:")
            if ch.upper() == 'I':
                opt.username = input("Your name:")
                opt.password = input("Password:")
            elif ch.upper() == "U":
                while True:
                    if not self.sign_up():
                        break
                return
            else:
                print("sorry!")
                return
        if not opt.password:
            opt.password = input("Password:")
        self.sign_in(opt.username, opt.password)

    def help(self, start=0):
        info = [
                '[-i][--ip]:指定要连接的ip', '[-P][--port]:指定端口号', '[-u][--user]:用户名', '[-p][--password]:密码',
                '默认连接localhost8880端口', '提供cd、mkdir、rm、ls的常见用法', '以及upload、download操作',
                '[cd]:切换当前目录，cd不带参数可返回当前目录', '[ls]:返回所要查询目录下的文件及子目录',
                '[mkdir]:创建新目录', '[rm]:删除指定目录', '[detail]:获取大小',  '[upload]:上传文件', '[download]:下载文件',
                '[sendto]:发送文件给指定用户', '[chatting]:进入聊天室',
                '[exit]:退出'
                ]
        if not start:
            [print(inf) for inf in info[0:5]]
        else:
            [print(inf) for inf in info[5:]]

    def info_pack(self, do, **argvs):
        # 将要发送的消息打包，便于发送及服务端识别
        argvs['do'] = do
        return json.dumps(argvs).encode('utf-8')

    def sign_up(self):
        # 注册函数
        self.sock.sendall(self.info_pack('validate'))
        invite_code = input('input your invite code:')
        self.sock.sendall(invite_code.encode("utf8"))
        passed = self.sock.recv(1).decode("utf8")
        if passed != 'Y':
            print('Wrong code')
            return 0
        user = input("input a username:")
        pw = input("put your code:")
        if pw == input("make sure your code:"):
            self.sock.sendall(self.info_pack('sign_up', user=user, pwd=pw))
            data = self.sock.recv(1024).strip().decode("utf-8")
            if data == 'ok':
                self.act(user)
                return 0
            else:
                print(data)
                if input("Again?[Y/N]").upper() == 'Y':
                    return 1
        else:
            if input("two different code,again?[Y/N]").upper() == 'Y':
                return 1

    def sign_in(self, user, pw):
        # 登录函数
        self.sock.sendall(self.info_pack('auth', user=user, pwd=pw))
        data = self.sock.recv(1024).strip().decode('utf-8')
        if data == 'ok':
            self.act(user)
        elif data == 'out':
            return
        else:
            print(data)
            self.sign_in(input("Your name:"), input("Password:"))

    def act(self, user):
        # 用户进入后所有的操作在这里识别发送给服务器并执行相应的操作
        dirs = user
        print("Welcome to ftp server...{}".format(user))
        while True:
            cmd = input('\r' + dirs + '>')
            if cmd == 'help':
                self.help(1)
                continue
            if cmd:
                self.sock.sendall(cmd.encode("utf8"))
                response = self.sock.recv(1024).decode("utf8").strip()
                # print(response,type(response))
                if response:
                    res = json.loads(response)
                    if res.get('exit'):
                        break
                    if res.get('dir'):
                        dirs = res['dir']
                    if res.get('note'):
                        print(res['note'])
                    if res.get('chat'):
                        print(res['chat'])
                        C_CHAT.name_get(user.encode())
                        C_CHAT.main()
                    if res.get('loop') == 'post':
                        file = cmd.split()[1]
                        file = os.path.abspath(file)
                        if os.path.isfile(file):
                            size = os.stat(file).st_size
                        else:
                            size = 0
                            print('file not exist')
                        msg = {'size': size}
                        # print(msg)
                        self.sock.sendall(json.dumps(msg).encode("utf8"))
                        ok = self.sock.recv(2) == b'ok'
                        if not ok:
                            print('Space full')
                            continue
                        if size:
                            seek = self.sock.recv(1024).decode('utf8')
                            f = open(file, 'rb')
                            f.seek(int(seek))
                            sent = int(seek)
                            while True:
                                if sent < size:
                                    data = f.read(1024)
                                    self.sock.sendall(data)
                                    sent += len(data)
                                    progress_bar(sent, size)
                                else:
                                    print("\nfinished")
                                    break
                            f.close()
                    if res.get('loop') == 'get':
                        cmd = cmd.split()
                        size = res.get('size')
                        seek = 0
                        file = ''
                        if len(cmd) == 3:
                            path, file = os.path.split(cmd[2])
                            if path and os.path.exists(path):
                                if file:
                                    file = cmd[2]
                                    f = open(cmd[2], 'ab+')
                                    if os.path.isfile(cmd[2]):
                                        seek = os.stat(cmd[2]).st_size
                                else:
                                    file = path + '\\' + res.get('file')
                            else:
                                print('path not found,save at ./')
                                file = res.get('file')
                        else:
                            file = res.get('file')
                        if os.path.isfile(file):
                            seek = os.stat(file).st_size
                        f = open(file, 'ab+')
                        if seek:
                            if not input("continue with any inputs:"):
                                print('Reload..')
                                seek = 0
                        f.seek(seek)
                        self.sock.sendall(str(seek).encode('utf8'))
                        while True:
                            if seek < size:
                                data = self.sock.recv(1024)
                                f.write(data)
                                seek += len(data)
                                progress_bar(seek, size)
                            else:
                                print('\nfinished')
                                break
                        f.close()


def progress_bar(have, all):
    # 进度条，
    # have：已经传送的
    # all：总共需要传送的
    done = have/all*100
    info = '|' + '#' * int(done/2)
    print('\r' + '{:.2f}%'.format(done) + info, end='')


if __name__ == "__main__":
    cs = ClientSocket()

