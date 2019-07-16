#include <stdlib.h>
#include <sys/types.h>
#include <stdio.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <string.h>
#include<time.h>
#include <unistd.h>
#include<pthread.h>
#define BUFFSIZE 1024

int socket_fd;  //全局变量，方便参数传递
//保存信息
int fds[10]={0};
char nick_name[10] [10];        //这里用数组指针会出问题
int mode[10]={0};

//定义管理员参数
struct
{
    char name[10];
    int mode;
}cjm,xjh,lgg;

void init()                     //初始化socket
{
    strncpy(cjm.name,"cjm",3);
    cjm.mode = 2;
    strncpy(xjh.name,"xjh",3);
    xjh.mode = 1;
    strncpy(lgg.name,"lgg",3);
    lgg.mode = 1;

    struct sockaddr_in myaddr;
    struct sockaddr_in client_addr;
    socket_fd = socket(AF_INET,SOCK_STREAM,0);
    if(socket_fd<0){
        printf("creat socket failure!\n");
        _exit(-1);
    }
    //printf("fd=%d\n",socket_fd);

    myaddr.sin_family = AF_INET;
    myaddr.sin_port = htons(8888);
    myaddr.sin_addr.s_addr = inet_addr("192.168.0.232");

    int ret = bind(socket_fd,(struct sockaddr*)&myaddr,sizeof(struct sockaddr));
    if(ret<0)
    {
        printf("bind failure\n");
        _exit(-1);
    }
    listen(socket_fd,5);    
}

char* online(char *onl)             //获得在线人数
{
    int i;
    char info[200]={0};
    for(i=0;i<10;i++)
        if(fds[i])
        {
            char str[20];
            sprintf(str,"%d--%s\n",i,nick_name[i]);
            //puts(str);
            strcat(info,str);
        }
    onl=info;
    return onl;
}

char * g_time(char *t)              //获得服务器时间
{
    time_t now;
    struct tm *tm_now;
    time(&now);
    tm_now = localtime(&now);
    //char t[20];
    sprintf(t,"%d-%d-%d %d:%d:%d\n",
        tm_now->tm_year+1900, tm_now->tm_mon+1, tm_now->tm_mday, tm_now->tm_hour, tm_now->tm_min, tm_now->tm_sec);
    return t;
}

int number(int fd)            //由fd获得此客户端的位置
{
    int i;
    for(i=0;i<10;i++) if(fds[i]==fd) return i;
    return -1;
}

int num(char *name)            //由name获得此客户端的位置
{
    int i;
    for(i=0;i<10;i++) if(strncmp(nick_name[i],name,10)==0) return i;
    return -1;
}

int on(int fd1,int fd2)     //取消禁言
{
     char msg[64];
     if(mode[number(fd1)]>0)
     {
        if(mode[number(fd2)] == -1)         //根据mode值判断有无权力
            mode[number(fd2)] = 0;
        else
            return 0;
        return 1;
     }
     else
        return -1;                      //不同返回值对应不同信息
}

int off(int fd1,int fd2)            //禁言
{
     char msg[64];
     if(mode[number(fd1)]>0)
     {
        if(mode[number(fd1)]>mode[number(fd2)])
            mode[number(fd2)] = -1;     //mode=-1则表示禁言
        else
            return 0;
        return 1;
     }
     else
        return -1;              //不同返回值对应不同信息
}

int chat_(int fd1,int fd2)    //通过服务端与某人连接
{
    char buf[BUFFSIZE]={0};
    recv(fd1,buf,sizeof(buf),0);        //服务端先接收客户端消息，再把它发送给指定客户端
    if(!strncmp(buf,"quit",4))          //收到quit则退出聊天
    {
        send(fd1,"chat over",10,0);
        printf("%s disconected with %s\n",nick_name[number(fd1)],nick_name[number(fd2)]);
        return 0;
    }
    char t[20];
    char info[BUFFSIZE]={0};
    sprintf(info,"%s:%s  -->%s",nick_name[number(fd1)],buf,g_time(t));
    send(fd2,info,sizeof(info),0);        //发送给指定客户端
    return 1;
}

int group(int fd)
{
    char buf[BUFFSIZE] = {0};
    recv(fd,buf,sizeof(buf),0);
    if(!strlen(buf))    return 1;   //buf为空直接下一次输入
    if(!strncmp(buf,"quit",4))
    {
        send(fd,"leave group chat",16,0);
        return 0;
    }
    if(!strncmp(buf,"off",3))
    {
        send(fd,"choose someone you want to stop his talk:\n",64,0);
        char *str;
        send(fd,online(str),200,0);
        recv(fd,buf,sizeof(buf),0);
        int i=(int)buf[0]-48;
        if(i<sizeof(fds)/4 && fds[i]>0)
        {
            char msg[64]={0};
            int ret = off(fd,fds[i]);
            if(ret>0)   strncpy(msg,"Successful!",11);
            else if(ret==0)    strncpy(msg,"Your rights is not enough!",32);
            else    strncpy(msg,"You are not administrator.Come on to improve yourself ha!",60);
            send(fd,msg,sizeof(msg),0);
        }
        else    send(fd,"The people not online!",32,0);
        return 1;
    }
    if(!strncmp(buf,"on",2))
    {
        send(fd,"choose someone you want to recover his talk:\n",64,0);
        char *str;
        send(fd,online(str),200,0);
        recv(fd,buf,sizeof(buf),0);
        int i=(int)buf[0]-48;
        if(i<sizeof(fds)/4 && fds[i]>0)
        {
            char msg[64];
            int ret = on(fd,fds[i]);
            if(ret>0)   strncpy(msg,"Successful!",12);
            else if(ret==0)    strncpy(msg,"The people is speakable!",32);
            else    strncpy(msg,"You are not administrator.Come on to improve yourself ha!",60);
            send(fd,msg,sizeof(msg),0);
        }
        else    send(fd,"The people is not exist!",32,0);
        return 1;
    }
    if(mode[number(fd)]<0)  send(fd,"You were not allowed to speak.Please call your boss!",64,0);
    else
    {
        int i;
        for(i=0;i<sizeof(fds)/4;i++)
            if(fds[i]>0 && fds[i] != fd)
            {
                char t[20];
                char info[BUFFSIZE]={0};
                sprintf(info,"%s##group chat##:\n%s  -->%s",nick_name[number(fd)],buf,g_time(t));
                send(fds[i],info,sizeof(info),0);
                break;
            }
        return 1;
    }
}

int accept_user()           //接受客户端并保存用户信息
{
    char buf[BUFFSIZE] = {0};
    int fd = accept(socket_fd,NULL,NULL);
    if (fd == -1){
        printf("connected fail...\n");
        return -1;
    }
    int i = 0;
    for (i = 0;i < 10;i++)
        if (fds[i] == 0)
        {
            //记录客户端的socket
            fds[i] = fd;
            break;
        }
    //printf("-------------%d",i);
    if (10 == i)
    {
        //同时连接超过10个则阻止
        char* str = "It's busy now,try again later!";
        send(fd,str,strlen(str),0);
        close(fd);
        sleep(5);
        return 0;
    }
    recv(fd,buf,BUFFSIZE,0);
    strncpy(nick_name[i],buf,10);       //保存用户昵称

    //不同成员不同权限
    if(strcmp(cjm.name,nick_name[i])==0)
        mode[i] = cjm.mode;
    else if(strcmp(xjh.name,nick_name[i])==0)
        mode[i] = xjh.mode;
    else if(strcmp(lgg.name,nick_name[i])==0)
        mode[i] = lgg.mode;
    else
        mode[i] = 0;
    printf("Welcome-----:%s!\n",nick_name[i]);

    return i;
}

void* service(void *p)          //每接入一个客户端就执行此函数，提供服务，线程函数
{
    int fd=*(int*)p;
    char buf[BUFFSIZE]={0};
    while(1)
    {
        //根据收到的消息执行不同操作
        if(recv(fd,buf,sizeof(buf),0)<0)        //可防止客户端意外终止，服务却仍在运行
        {
            close(fd);
            fds[number(fd)]=0;
            break;
        }
        if(!strncmp(buf,"exit",4))
        {
            printf("%s leave chating room!\n",nick_name[number(fd)]);
            send(fd,"Thanks for using!",64,0);
            fds[number(fd)]=0;
            send(fd,"exit",4,0);
            close(fd);
            break;
        }

        else if(!strncmp(buf,"@",1))
        {
            if(buf[1]!='\0')            //判断@后面是否指定名字
            {
                char name[10] = {0};
                int i;
                for(i=0;buf[i+1]!='\0'&&i<10;i++)
                    name[i] = buf[i+1];
                i = num(name);
                if(i>=0)
                {
                    printf("%s connecting to %s...\n",nick_name[number(fd)],nick_name[i]);
                    char info[20];
                    sprintf(info,"chating with %s",nick_name[i]);
                    send(fd,info,32,0);
                    while(1)   if(chat_(fd,fds[i])==0) break;
                }
                else    send(fd,"The people not online!",32,0);
                continue;       //继续下一个循环跳过下面语句
            }
            //没有指定名字则由用户选择
            send(fd,"choose someone you want to chat with the number!\n",64,0);
            char *str;
            send(fd,online(str),256,0);
            recv(fd,buf,sizeof(buf),0);
            int i=(int)buf[0]-48;
            if(i<sizeof(fds)/4 && fds[i]>0)
            {
                printf("%s connecting to %s...\n",nick_name[number(fd)],nick_name[i]);
                char info[20];
                sprintf(info,"chating with %s",nick_name[i]);
                send(fd,info,32,0);
                while(1)   if(chat_(fd,fds[i])==0) break;
            }
            else    send(fd,"The people not online!",32,0);
        }

        else if(!strncmp(buf,"group",5))
        {
            send(fd,"welcome to group chat!",32,0);
            while(1)   if(group(fd)==0) break;
        }

        else if(!strncmp(buf,"online",6))
        {
            char *str;
            send(fd,online(str),200,0);
        }

        else if(!strncmp(buf,"time",4))
        {
            char str[20];
            send(fd,g_time(str),20,0);
        }

        else if(!strncmp(buf,"name",4)) send(fd,nick_name[number(fd)],10,0);

        else if(!strncmp(buf,"fd",2))
        {
            char fd_[3];
            sprintf(fd_,"%d",fd);
            send(fd,fd_,5,0);
        }

        else send(fd,buf,sizeof(buf),0);        //不是特殊字符串则把消息原封不动发回去

    }
}

int main()
{
    init();         //socket初始化
    while(1)
    {
        int i = accept_user();      //等待客户端接入
        if(i>-1)
        {
            pthread_t tid;
            if(pthread_create(&tid,0,service,fds+i)==0)      printf("聊天室服务线程启动\n"); //并发
            else
            {
                printf("聊天室发生错误，正在退出...\n");
                close(fds[i]);
            }
        }
    }
    return 0;

}
