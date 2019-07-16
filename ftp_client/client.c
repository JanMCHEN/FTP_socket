#include <stdlib.h>
#include <sys/types.h>
#include <stdio.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <string.h>
#include <unistd.h>
#include<pthread.h>
#define BUFFSIZE 1024

char names[10];

void* receive(void *p)      //收消息线程函数，保证任何时候都能收到服务端消息
{
    int fd=*(int*)p;
    int times=0;
    while(1)
    {
        char buf[BUFFSIZE]={0};
        int ret=recv(fd,buf,BUFFSIZE,0);
        if(!ret){
            times++;
            if(times<10) continue;
            //printf("leave chating room\n");
            break;          //收到空超过10次则判定为此连接已关闭，可以防止fd关闭线程却没退出
        }
        times=0;
        if(!strncmp(buf,"exit",4)) break;   //收到exit则退出线程
        printf("<<%s\n",buf);
    }
    close(fd);
    return NULL;
}

void help()                 //打印帮助消息
{
    printf("本聊天程序由多线程c语言编程实现，默认发消息服务端返回原消息，并实现了一些基本功能，下面仅对几个已经实现的功能作简要说明:\n");
    printf("[@][name]:直接@或者指定用户可以实现向对方发送消息\n");
    printf("[name]:获取用户名\n[fd]:查看当前fd值\n[time]:查看时间\n[online]:查看当前在线人数\n"
    "[group]:进入群聊，群聊里可以实现[off]禁言，[on]取消禁言\n");
}

void name_get(char* name)
{
    strncpy(names,name,10);
}

int main()
{
    char buf[BUFFSIZE] = {0};
    struct sockaddr_in server_addr;
    int fd = socket(AF_INET,SOCK_STREAM,0);
    if(fd<0){
        printf("creat socket failure!\n");
        return -1;
    }
    //printf("fd=%d\n",fd);
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(8888);
    server_addr.sin_addr.s_addr = inet_addr("127.0.0.1");

    if(connect(fd,(struct sockaddr*)&server_addr,sizeof(struct sockaddr))<0)
    {
        printf("connect fail to chatting room\n");
        return 0;
    }
    strncpy(buf,names,sizeof(names));
    memset(names,0,strlen(names));
    //如果没传则输入name
    if(!strlen(buf))
    {
        printf("input your nick name-----:");
        scanf("%s",buf);
    }
    char name[10];
    strncpy(name,buf,10);
    send(fd,buf,sizeof(buf),0);  //发给服务端用户昵称
    memset(buf,0,strlen(buf));  //buf清0
    printf("Welcome...\n");
    pthread_t tid;
    if(pthread_create(&tid,NULL,receive,&fd)<0) printf("聊天线程启动失败");  //并发，保持随时能收到消息
    else
    while(1)
    {
        sleep(1);       //等待服务器回复，降低发消息频率
        printf("%s>>:",name);
        scanf("%[^\n]",buf);   //输入带空格的字符串,只在遇到\n时结束输入
        getchar();  //获得'\n'，否者scanf还没接受下一个输入就遇到\n
        if(!strncmp(buf,"help",4))     //获取帮助消息
        {
            help();
            continue;
        }
        //if(!strlen(buf))    continue;               //没发送内容则继续
        if(send(fd,buf,BUFFSIZE,0)<0)   break;      //发送失败则退出，防止连接意外关闭没来得及响应
        memset(buf,0,strlen(buf)); //buf清0
    }
    printf("Back to ftp server..\n");
    return 0;
}
