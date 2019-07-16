# ftp_socket
python3 ftp and c chat

ftp服务器采用python编写，在python3.6.7下运行成功。
ftp_service文件夹下存放服务端程序，其bin下有run.py 可直接python run.py help查看帮助信息，主要代码存于core目录下，User为用户目录，conf存放配置文件。
ftp_client下有客户端代码，可直接python client.py help 查看帮助信息。

代码为单片机课设要求设计，能通过socket收发文件，多人聊天，其中收发文件用python3编写，聊天采用c代码编写，可以单独使用其中一个，支持多用户持久登录，用户密码以json格式保存在本地，支持常用的cd,ls,pwd,rm等操作，离线发送文件暂存等
