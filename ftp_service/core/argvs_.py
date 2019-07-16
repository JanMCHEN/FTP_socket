import optparse
import socketserver
from conf.settings import *
from core import server


class ArgvHandler():
    def __init__(self):
        self.op = optparse.OptionParser()
        self.op.add_option("-i", "--ip_addr", dest="ip_addr")
        self.op.add_option("-P", "--port", dest="port")
        options, args = self.op.parse_args()
        self.verify_args(options, args)

    def verify_args(self, opt, args):
        if not opt.ip_addr:
            opt.ip_addr = IP
        if not opt.port:
            opt.port = PORT
        self.ip_port = (opt.ip_addr, int(opt.port))
        if args:
            if hasattr(self, args[0]):
                getattr(self, args[0])()

    def start(self):
        print("start...")
        sock = socketserver.ThreadingTCPServer(self.ip_port, server.ServerSocket)
        # sock.allow_reuse_address = True
        sock.serve_forever()

    def help(self):
        info = ['[-i][--ip]:指定绑定的ip，默认绑定localhost', '[-P][--port]:指定端口号，默认8888',
                '配置参数>>:', 'start:启动', 'help:帮助信息', 'more:更多信息']
        [print(inf) for inf in info]

    def more(self):
        print('敬请期待')
