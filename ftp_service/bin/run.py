import socketserver
import os, sys
# 解决arm编码问题
import codecs
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PATH)
from core import argvs_


if __name__ == "__main__":
    argvs_.ArgvHandler()
