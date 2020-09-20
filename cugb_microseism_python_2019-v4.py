# -*- coding: utf-8 -*-

#导入相应库函数
import requests
from bs4 import BeautifulSoup
import json
from requests.exceptions import ReadTimeout
from relay_config import relay_config

# 创建session对象，可以保存Cookie值
ssion = requests.session()

# 处理 headers
headers = {
'user-agent': 'Mozilla / 5.0(Windows NT 10.0; WOW64) AppleWebKit / ' +
	'537.36(KHTML, likeGecko) Chrome / 53.0.2785.104Safari / ' +
	'537.36Core / 1.5	3.4882.400QQBrowser / 9.7.13059.400'}

#中心站用户号存储 & 中间信息 & 最终信息存储
ceter_station_numbers = ["242","243","244","245","246","247"]
center_station_data = {}
station_data = {}
micro_var = {}
micro_station_data = []

# 登录密码 及 相关参数保存
data = {"login_pwd":"admin"}
sysinfo_param = {"opcode":"2"} 
wireless_status_param = {"opcode":"2","wlanid":"1"}
wireless_clientlist_param = {"opcode":"1","wlanid":"1"} 

#工作时间格式转换
def time_change(t):
	if(int(t) > 3600):
		t_change = str(int(t)//3600)+'h'+str(int(t)//60%60)+'m'+str(int(t)%60)+'s'
	else:
		t_change = str(int(t)//60)+'m'+str(int(t)%60)+'s'
	return t_change
		
#定义获取数据的函数
def get_status(number):
	try:
		# 发送附带用户名和密码的请求，并获取登录后的Cookie值，保存在ssion里
		ssion.post("http://172.16.13." + number + "/cgi-bin/showhtml?page=login.html", data = data,timeout = 0.5)
	
		#获取希望的到的数据所在网页的信息
		sysinfo = requests.post("http://172.16.13." + number + "/cgi-bin/sysinfo",params = sysinfo_param)
		wireless_status = requests.post("http://172.16.13." + number + "/cgi-bin/wireless_status",params = wireless_status_param)
		wireless_clientlist = requests.post("http://172.16.13." + number + "/cgi-bin/wireless_clientlist",params = wireless_clientlist_param)
		
		sysinfo_record = sysinfo.json()			#将网页返回的json信息转换成字典
		wireless_status_record = wireless_status.json()		
		wireless_clientlist_record = wireless_clientlist.json()
		
		#将需要的数据存储在字典中
		center_station_data['number'] = number
		center_station_data['connect'] = "connect"
		center_station_data['system_up_time'] = time_change(sysinfo_record['system_up_time'])
		center_station_data['cpu_usage'] = sysinfo_record['cpu_usage'] + '%'
		center_station_data['mem_usage'] = str(int(sysinfo_record['mem_usage'])-15) + '%'
		center_station_data['channel'] = wireless_status_record['wlan_channel']
		center_station_data['count'] = wireless_clientlist_record['ItemList']['count']
		
		#对采集站数据进行处理
		micro_var.clear()
		for i in range(int(center_station_data['count'])):
			micro_var[i] = {}
			micro_var[i]['number'] = number
			try:
				mac = wireless_clientlist_record['ItemList']['data'][i]['mac']
				micro_var[i]['relay_station'] = relay_config(mac)
			except:		
				micro_var[i]['relay_station'] = "error"
			micro_var[i]['connecttime'] = time_change(wireless_clientlist_record['ItemList']['data'][i]['connecttime'])
			micro_var[i]['rssi'] = str(int(wireless_clientlist_record['ItemList']['data'][i]['rssi'])-95)+'dBm'
			micro_var[i]['txpakets'] = wireless_clientlist_record['ItemList']['data'][i]['txpakets']
			micro_var[i]['rxpakets'] = wireless_clientlist_record['ItemList']['data'][i]['rxpakets']

		return center_station_data
		
	#页面访问超时时提示未连接路由器
	except:
		center_station_data['number'] = number
		center_station_data['connect'] = "unconnect"
		center_station_data['system_up_time'] = '0'
		center_station_data['cpu_usage'] = "0"
		center_station_data['mem_usage'] = '0'
		center_station_data['channel'] = '0'
		center_station_data['count'] = '0'
		
		return center_station_data
	
		
		
		
#创建文件，调用函数，得到需要信息
target = open("CenterStationStatus.txt", 'w')
target.truncate()
for number in ceter_station_numbers:
	station_data[number] = get_status(number)
	
	#将中心站数据写入文件中
	for info,infos in station_data[number].items():
		target.write(infos)
		target.write(" ")

	#输入采集站数据
	if(int(station_data[number]['count'])>0):
		target_micro = open("micro_connect_"+number+".txt", 'w')
		target_micro.truncate()
		for i in range(int(station_data[number]['count'])):
			for info,infos in micro_var[i].items():
				target_micro.write(infos)
				target_micro.write(" ")
			target_micro.write("\n")
		target_micro.close()
	target.write("\n")
target.close()
			
		
