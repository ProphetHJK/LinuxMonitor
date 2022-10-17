# -*- coding: utf-8 -*-
import os
import time
import logging
import wechatpush
import psutil
import ping3
import re
from configparser import ConfigParser
from datetime import datetime

# Return CPU temperature as a character string


def getCPUtemperature(file, scaler):
    cputemp = 0
    rawline = os.popen('cat %s' % file).readline()
    try:
        cputemp = int(rawline) // int(scaler)
    except Exception as ex:
        logging.error("%s", ex)
        cputemp = 0

    return cputemp

# Return RAM information (unit=kb) in a list
# Index 0: total RAM
# Index 1: used RAM
# Index 2: free RAM


def getRAMinfo():
    p = os.popen('free')
    i = 0
    while 1:
        i = i + 1
        line = p.readline()
        if i == 2:
            return (line.split()[1: 4])

# Return % of CPU used by user as a character string


def getCPUuse():
    # cpuusagestr = os.popen("top -n1 | awk '/Cpu\(s\):/ {print $2}'").readline()
    # logging.info(cpuusagestr)
    cpuusagefloat = psutil.cpu_percent()
    return cpuusagefloat

# Return information about disk space as a list (unit included)
# Index 0: total disk space
# Index 1: used disk space
# Index 2: remaining disk space
# Index 3: percentage of disk used


def getDiskSpace(mount_point):
    p = os.popen("df %s" % mount_point)
    i = 0
    while 1:
        i = i + 1
        line = p.readline()
        if i == 2:
            return (line.split()[1: 5])


def get_info():

    # CPU informatiom
    CPU_temp = getCPUtemperature()
    CPU_usage = getCPUuse()

    # RAM information
    # Output is in kb, here I convert it in Mb for readability
    RAM_stats = getRAMinfo()
    RAM_total = round(int(RAM_stats[0]) / 1024, 1)
    RAM_used = round(int(RAM_stats[1]) / 1024, 1)
    RAM_free = round(int(RAM_stats[2]) / 1024, 1)

    # Disk information
    DISK_stats = getDiskSpace()
    DISK_total = DISK_stats[0]
    DISK_used = DISK_stats[1]
    DISK_left = DISK_stats[2]
    DISK_perc = DISK_stats[3]

    logging.info(
        "\nLocal Time {timenow} \n"
        "CPU Temperature = {CPU_temp}\n"
        "CPU Use = {CPU_usage} %\n"
        "RAM Total = {RAM_total} MB\n"
        "RAM Used = {RAM_used} MB\n"
        "RAM Free = {RAM_free} MB\n\n"
        "DISK Total Space = {DISK_total}B\n"
        "DISK Used Space = {DISK_used}B\n"
        "DISK Left Space = {DISK_left}B\n"
        "DISK Used Percentage = {DISK_perc}\n"
        "".format(
            timenow=time.asctime(time.localtime(time.time())),
            CPU_temp=CPU_temp,
            CPU_usage=CPU_usage,
            RAM_total=str(RAM_total),
            RAM_used=str(RAM_used),
            RAM_free=str(RAM_free),
            DISK_total=str(DISK_total),
            DISK_used=str(DISK_used),
            DISK_left=str(DISK_left),
            DISK_perc=str(DISK_perc),
        )
    )


CPU_temp_flag = 0
CPU_usage_flag = 0
RAM_free_flag = 0
DISK_left_flag = 0
ping_flag = 99


def monitor(corpid, agentid, secret, cpu_temperature_file, cpu_temperature_scaler, disk_mount_point,
                ping_siteorip, cpu_temperature_threshold, cpu_usage_threshold, ram_free_threshold, 
                ping_error_count_threshold, disk_free_threshold, pc_power_switch, service_switch, 
                service1_name, service2_name):
    global CPU_temp_flag
    global CPU_usage_flag
    global RAM_free_flag
    global DISK_left_flag
    global ping_flag
    
    # cpu温度监控
    if CPU_temp_flag == 0:
        CPU_temp = getCPUtemperature(cpu_temperature_file,cpu_temperature_scaler)
        logging.info("cpu temperature:%d C" % CPU_temp)
        # 是否超过55度
        if CPU_temp > int(cpu_temperature_threshold):
            CPU_temp_flag = 10
            wechatpush.send_to_wecom(
                "cpu temperature:%d C" % CPU_temp, corpid, agentid, secret)
    elif CPU_temp_flag > 0:
        CPU_temp_flag = CPU_temp_flag - 1

    # cpu占用监控
    CPU_usage = getCPUuse()
    logging.info("cpu usage:{CPU_usage} %".format(
            CPU_usage=str(CPU_usage)))
    if CPU_usage > int(cpu_usage_threshold):
        wechatpush.send_to_wecom("cpu usage:{CPU_usage} %".format(
            CPU_usage=str(CPU_usage)), corpid, agentid, secret)
    RAM_stats = getRAMinfo()
    RAM_free = round(int(RAM_stats[2]) / 1024, 1)
    if RAM_free < int(ram_free_threshold):
        wechatpush.send_to_wecom("ram free:%d MB" %
                                 RAM_free, corpid, agentid, secret)
    # 磁盘监控
    if DISK_left_flag == 0:
        DISK_stats = getDiskSpace(disk_mount_point)
        DISK_left = int(DISK_stats[2]) // 1000000
        logging.info("disk free:%d GB" %DISK_left)
        if DISK_left < int(disk_free_threshold):
            DISK_left_flag = 10
            wechatpush.send_to_wecom("disk free:%d GB" %
                                     DISK_left, corpid, agentid, secret)
    elif DISK_left_flag > 0:
        DISK_left_flag = DISK_left_flag - 1

    # 网络监控
    logging.info("ping_flag:%d" % ping_flag)
    pingresult = ping3.ping(ping_siteorip)
    if pingresult is None:
        logging.info("network error")
        wechatpush.send_to_wecom("network error", corpid, agentid, secret)
        if ping_flag != 99:
            ping_flag = ping_flag + 1
            if ping_flag >= int(ping_error_count_threshold):
                logging.info("network error,reboot now!")
                # TODO:添加重启命令
                ping_flag = 99
                wechatpush.send_to_wecom(
                    "network error,reboot now!", corpid, agentid, secret)
    else:
        logging.info("ping status:{}".format(pingresult))
        ping_flag = 0

    # PC监控
    if int(pc_power_switch) == 1:
        pingresult = ping3.ping("192.168.123.3")
        if pingresult is None:
            logging.info("pc is poweroff now")
        else:
            logging.info("pc is power on now")
            wechatpush.send_to_wecom("pc is power on now", corpid, agentid, secret)

    # 服务监控
    if int(service_switch) == 1:
        service1_status = "".join(os.popen("service %s status" % service1_name).readlines())
        service1_active = re.search(".*Active: (.*) \(.*",service1_status).group(1)
        service2_status = "".join(os.popen("service %s status" % service2_name).readlines())
        service2_active = re.search(".*Active: (.*) \(.*",service2_status).group(1)
        wechatpush.send_to_wecom("*%s:\n%s\n*%s:\n%s" % (service1_name,service1_active,service2_name,service2_active), corpid, agentid, secret)


if __name__ == '__main__':
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 加载参数
    config = ConfigParser()
    config_file_path = os.path.join(current_dir,'config.ini.bak')
    config.read(config_file_path, encoding='utf-8')
    corpid = config['wechatpush']['corpid']
    agentid = config['wechatpush']['agentid']
    secret = config['wechatpush']['secret']
    cpu_temperature_file = config['monitor']['cpu_temperature_file']
    cpu_temperature_scaler = config['monitor']['cpu_temperature_scaler']
    disk_mount_point = config['monitor']['disk_mount_point']
    ping_siteorip = config['monitor']['ping_siteorip']
    time_interval = config['monitor']['time_interval']
    service1_name = config['monitor']['service1_name']
    service2_name = config['monitor']['service2_name']
    cpu_temperature_threshold = config['threshold']['cpu_temperature_threshold']
    cpu_usage_threshold = config['threshold']['cpu_usage_threshold']
    ram_free_threshold = config['threshold']['ram_free_threshold']
    ping_error_count_threshold = config['threshold']['ping_error_count_threshold']
    disk_free_threshold = config['threshold']['disk_free_threshold']
    log_file_path = config['log']['log_file_path']
    pc_power_switch = config['switch']['pc_power_switch']
    service_switch = config['switch']['service_switch']
    start_hour_day = config['monitor']['start_hour_day']
    end_hour_day = config['monitor']['end_hour_day']
    start_day_week = config['monitor']['start_day_week']
    end_day_week = config['monitor']['end_day_week']


    # get info
    logger_file = os.path.join(log_file_path)
    handlers = [logging.FileHandler(logger_file, mode='w')]
    logging.basicConfig(format='%(asctime)s - %(pathname)s[line:%(lineno)d] '
                        '- %(levelname)s: %(message)s',
                        level=logging.INFO,
                        handlers=handlers)
    ret = wechatpush.send_to_wecom("linux monitor start!", corpid, agentid, secret)
    logging.info(ret)


    while(True):
        logging.info('weekday:{},hour:{},start_hour_day:{},end_hour_day:{},start_day_week:{},end_day_week:{}'.format(datetime.today().weekday(),datetime.now().hour,start_hour_day,end_hour_day,start_day_week,end_day_week))
        if (datetime.today().weekday()+1) <= int(end_day_week) and (datetime.today().weekday()+1) >= int(start_day_week):
            if datetime.now().hour <= int(end_hour_day) and datetime.now().hour >= int(start_hour_day):
                logging.info('run monitor')
                monitor(corpid, agentid, secret, cpu_temperature_file, cpu_temperature_scaler, disk_mount_point,
                        ping_siteorip, cpu_temperature_threshold, cpu_usage_threshold, ram_free_threshold, 
                        ping_error_count_threshold, disk_free_threshold, pc_power_switch, service_switch, 
                        service1_name, service2_name)
        time.sleep(int(time_interval))  # Time interval for obtaining resources
