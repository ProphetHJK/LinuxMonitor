# Linux开发板运行状态监控及推送

## 主要功能

- CPU占用异常报警
- 内存占用异常报警
- 温度异常报警
- 网络异常自动重启(未测试)
- 磁盘占用异常报警

## 使用方法

### 注册微信企业号

用于免费接受推送消息

教程地址：<https://github.com/easychen/wecomchan>

拿到`企业Id`,`应用secret`,`应用ID`就行

### 填写配置文件

根据config.ini中注释文件填写对应参数

### 安装python3及依赖

略(不会连这个都不会吧)

### 运行程序

注意别用root用户运行

python3 main.py

### 设置为自启动服务

仅针对debian系，包括debian，ubuntu等

修改opi4monitor.service

注册服务
