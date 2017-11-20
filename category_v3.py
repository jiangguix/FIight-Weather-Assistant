# -*- coding: UTF-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf8')

import urllib
import urllib2
import time
import datetime
import calendar as cld
import re
import math
from bs4 import BeautifulSoup

#判断是否为数字
def is_number(word):
	try:
		int(word)
		return True
	except ValueError:
		return False

#找出云组中的最小值，或者能见度中的最低值
def find_min(word):
	temp = re.split('TEMPO:|turn:|PROB40:|PROB30:',word.replace(' ',''))
	while '' in temp:
		temp.remove('')

	if 'SM' in word:
		visvalue = []
		for i in range(len(temp)):
			ind = temp[i].find('SM')
			if '/' in temp[i]:
				if len(temp[i]) == 6:
					visvalue.append(int(temp[i][:1])+float(temp[i][ind-3:ind-2])/float(temp[i][ind-1:ind]))
				else:
					visvalue.append(float(temp[i][ind-3:ind-2])/float(temp[i][ind-1:ind]))
			else:
				visvalue.append(int(temp[i][ind-1:ind]))
		return int(min(visvalue)*1600)
	elif is_number(temp[0]):
		for i in range(len(temp)-1):
			if int(temp[i+1]) > int(temp[i]):
				temp[i+1] = temp[i]
		return int(temp[-1])
	elif 'VV' in word:
		for item in temp:
			if 'VV' in item:
				return int(temp[-1][3:5])*30
	elif ('FEW' in word) or ('BKN' in word) or ('SCT' in word) or ('OVC' in word):
		for i in range(len(temp)-1):
			if int(temp[i+1][3:6]) > int(temp[i][3:6]):
				temp[i+1] = temp[i]
		return int(temp[-1][3:6])*30
	else:
		return -999

#判断类别（风组、云组、能见度、天气现象），返回类别名称
def category(word):
	f = open('weather.txt','r')
	weather = []
	for line in f.readlines():
		weather.append(line.split()[1])
	f.close()

	if ('MPS' in word) or ('KT' in word):
		return 'wind'
	elif ('FEW' in word) or ('BKN' in word) or ('SCT' in word) or ('OVC' in word) or ('VV' in word):
		return 'cloud'
	elif ('SM' in word) or (is_number(word) and len(word) < 5):
		return 'vis'
	elif word.strip() in weather:
		return 'weather'
	else:
		return 'Unknown'

#解码风组，分解成风向风速
def winddecode(word):
	direction = '风'
	mag = ''
	if 'VRB' in word:
		direction = ''
	elif (0<int(word[:3])<30) or (330<int(word[:3])<=360):
		direction =  '偏北'
	elif 30<=int(word[:3])<=60:
		direction = '东北'
	elif 60<int(word[:3])<120:
		direction = '偏东'
	elif 120<=int(word[:3])<=150:
		direction = '东南'
	elif 150<int(word[:3])<210:
		direction = '偏南'
	elif 210<=int(word[:3])<=240:
		direction = '西南'
	elif 240<int(word[:3])<300:
		direction = '偏西'
	elif 300<=int(word[:3])<=330:
		direction = '西北'

	if ('MPS' in word) and (int(word[3:5])>5):
		mag = '风' + str(int(word[3:5])) + 'mps'
		if 'G' in word:
			mag = mag + '，阵风' + str(int(word[6:8])) + 'mps'
	elif ('KT' in word) and (int(word[3:5])>11):
		mag = '风' + str(int(word[3:5])/2) + 'mps'
		if 'G' in word:
			mag = mag + '，阵风' + str(int(word[6:8])/2) + 'mps'
	elif ('MPS' in word) and ('G' in word):
		mag = '阵风' + str(int(word[6:8])) + 'mps'
	elif ('KT' in word) and ('G' in word):
		mag = '阵风' + str(int(word[6:8])/2) + 'mps'
	else:
		mag = '微风'

	return direction, mag

#分析报文，将天气、风、能见度、云组分别存入condition字典的对应key中
def analyze(word):
	condition = {'weather':'','wind':'','vis':'','cloud':''}

	for item in word.split():
		if category(item) == 'Unknown':
			continue
		else:
			condition[category(item)] = condition[category(item)] + ' ' + item

	return condition

#处理时间（跨天、跨月、跨年各种问题）
today = time.gmtime()
# today = [2017,12,31,4]
def time_analyze(t_day, t_hour): ##用于分析有日期出现的时间组，如1203/1305和FM120600
	if int(t_day) < today[2]:
		t_deltamonth = cld.monthrange(today[0],today[1])[1]
	else:
		t_deltamonth = 0
	if int(t_hour) == 24:
		t_hour = 0
		t_deltaday = 1
	else:
		t_deltaday = 0
	t_result = datetime.datetime(today[0],today[1],int(t_day),int(t_hour)) + datetime.timedelta(days = t_deltamonth + t_deltaday)
	return t_result

def time_analyze_2(t_text, t_flag): #用于分析无日期出现的时间组，如TEMPO 0408
	if int(t_flag[:2]) < today[2]:
		t_deltamonth = cld.monthrange(today[0],today[1])[1]
	else:
		t_deltamonth = 0

	if int(t_text[:2])<int(t_flag[2:4]):
		t_deltadayst = t_deltadayed = 1
	elif int(t_text[:2])>int(t_text[2:4]):
		t_deltadayst = 0
		t_deltadayed = 1
	else:
		t_deltadayst = t_deltadayed = 0

	if t_text[2:4] == '24':
		t_text[2:4] = '00'
		t_deltadayed = t_deltadayed + 1

	t_result_st = datetime.datetime(today[0],today[1],int(t_flag[:2]),int(t_text[:2])) + datetime.timedelta(days = t_deltadayst + t_deltamonth)
	t_result_ed = datetime.datetime(today[0],today[1],int(t_flag[:2]),int(t_text[2:4])) + datetime.timedelta(days = t_deltadayed + t_deltamonth)

	return t_result_st, t_result_ed

#核心1：从ADDS网站爬取TAF报并进行分解
#返回一个数组，长度为TAF报预报时长，每个元素为一个condition字典，代表这个小时的风、能见度、云、天气状态。
def decompose(airport, inputtstart, inputtend):
	# if airport == 'ZGSD':
	# 	return 
	
	#对于没有参与国际交换的南昌机场，从青岛空管网址爬取报文：
	if airport == 'ZSCN':
		url = 'http://report.qdatm.net/content.aspx?tt=FT&obcc=' + airport + '&includeBak=False&lastestCount=1&IPs='
		request = urllib2.Request(url=url)
		response = urllib2.urlopen(request, timeout=30)
		result = response.read()
		html = BeautifulSoup(result,'lxml').get_text()
		html = html.split('\n')[2]

		tafraw = html.split('TAF')[2].split('=')[0]

		taf = []
		char = ''
		for item in tafraw.split():
			if item in ['BECMG','TEMPO','PROB40','PROB30']:
				taf.append(char + tafraw.split(item,1)[0])
				tafraw = tafraw.split(item,1)[1]
				char = item
		taf.append(char + tafraw)
	else:
		url = 'https://www.aviationweather.gov/metar/data?ids=' + airport + '&format=raw&date=0&hours=0&taf=on'
		#headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.2; WOW64; rv:22.0) Gecko/20100101 Firefox/22.0'}
		request = urllib2.Request(url=url)
		response = urllib2.urlopen(request, timeout=30)
		result = response.read()

		html = BeautifulSoup(result,'lxml')
		tafraw = html.code.get_text()

		taf = tafraw
		title = ['TAF COR', 'TAF AMD', 'TAF']
		for item in title:
			if item in taf:
				taf = taf.strip(item)
		taf = taf.split(u' \xa0\xa0')

	#保存原始报文用于输出：
	tafraw = tafraw.replace(u' \xa0\xa0','\n    ')

	#有些国外报文最后会有INTER变化项，INTER和TEMPO类似，但INTER表示波动的时间长度在30分钟以内，TEMPO在30-60分钟
	if 'INTER' in taf[-1]:
		temp = taf[-1].split('INTER')
		taf[-1] = temp[0]
		for item in temp[1:]:
			taf.append('TEMPO ' + item)

	timestart = time_analyze(taf[0].split()[2][:2],taf[0].split()[2][2:4])
	#算报文有效时长，对于南昌机场，直接取24小时报
	if airport == 'ZSCN':
		timeend = timestart + datetime.timedelta(days = 1)
	else:
		timeend = time_analyze(taf[0].split()[2][5:7],taf[0].split()[2][7:9])
	timespan = (timeend-timestart).days*24 + (timeend-timestart).seconds/3600 + 1

	condition = []
	for i in range(timespan):
		condition.append(analyze(taf[0].split(' ',3)[3]))

	i = 1
	while i<len(taf):
		#有些国家报文TEMPO前加PROB，在ADDS上就会显示一行PROB空行，如遇到PROB30占一空行的情况，表示其后跟的tempo是30%概率的天气，通过i+=2跳过当前PROB行和其后tempo行：
		if 'PROB30' in taf[i] and len(taf[i].split())==1:
			i+=2
			continue

		if 'FM' in taf[i]:
			timemark = time_analyze(taf[i].strip()[2:4],taf[i].strip()[4:6])
			indstart = (timemark-timestart).days*24 + (timemark-timestart).seconds/3600
			for j in range(indstart,len(condition)):
				condition[j] = analyze(taf[i].split(' ',1)[1])

		if ('TEMPO' in taf[i]) or ('PROB40' in taf[i]):
			#有些国家报文TEMPO前加PROB，在ADDS上就会显示一行PROB空行，跳过该空行：
			if len(taf[i].split()) == 1:
				continue

			#但有时候格式会变为：PROB40 0810这种情况：
			if len(taf[i].split()[1]) == 4:
				timemarkst, timemarked = time_analyze_2(taf[i].split()[1], taf[0].split()[2][:4])
			#一般来讲TAF报格式形如：TEMPO 1803/1809
			else:
				timemarkst = time_analyze(taf[i].split()[1][:2],taf[i].split()[1][2:4])
				timemarked = time_analyze(taf[i].split()[1][5:7],taf[i].split()[1][7:9])

			indstart = (timemarkst-timestart).days*24 + (timemarkst-timestart).seconds/3600
			indspan = (timemarked-timemarkst).seconds/3600
	 		conditiontem = analyze(taf[i].split(' ',2)[2])

			for j in range(indstart,indstart+indspan):
				for key in condition[j].keys():
					if len(conditiontem[key])>1:
						condition[j][key] = condition[j][key] + ' ' + taf[i].split()[0] + ':' + conditiontem[key]

		if 'BECMG' in taf[i]:
			#对于BECMG 0507 这种情况：
			if len(taf[i].split()[1]) == 4:
				timemarkst, timemarked = time_analyze_2(taf[i].split()[1], taf[0].split()[2][:4])
			#对于一般情况BECMG 2905/2907：
			else:
				timemarkst = time_analyze(taf[i].split()[1][:2],taf[i].split()[1][2:4])
		
			indstart = (timemarkst-timestart).days*24 + (timemarkst-timestart).seconds/3600
	 		conditiontem = analyze(taf[i].split(' ',2)[2])

	 		#对于TEMPO 0106 ... BECMG 0304 ... 的情况，应保留前序TEMPO的信息：
	 		for j in range(indstart,len(condition)):
				for key in condition[j].keys():
					if len(conditiontem[key])>1 and ('TEMPO' in condition[j][key]):
						indtemp = condition[j][key].index('TEMPO')
						condition[j][key] = conditiontem[key] + ' ' + condition[j][key][indtemp:]
					elif len(conditiontem[key])>1 and ('PROB' in condition[j][key]):
						indtemp = condition[j][key].index('PROB')
						condition[j][key] = conditiontem[key] + ' ' + condition[j][key][indtemp:]
					elif len(conditiontem[key])>1:
						condition[j][key] = conditiontem[key]
		i+=1

	timest, timeed = time_analyze_2(inputtstart+inputtend, taf[0].split()[2][:4])
	#如果给定机场时间超过报文预报截至时间，则截断到报文截至时间
	if timeed > timeend:
		timeed = timeend

	print timest
	print timeed

	indst = (timest-timestart).days*24 + (timest-timestart).seconds/3600
	inded = (timeed-timestart).days*24 + (timeed-timestart).seconds/3600
	result = [condition[indst]]
	for i in range(indst+1,inded+1):
		if condition[i] != result[-1]:
			result.append(condition[i])
	return result, tafraw

#核心2，从accuweather网站上爬取温度预报信息，返回某一时刻温度：
def temperature(airport, t):

	aircode = {'ZSAM':'1834','ZSFZ':'1801','ZGSZ':'1831','YSSY':'361','YMML':'431','KLAX':'7721',
				'KJFK':'10358','KSEA':'8549','CYVR':'1332','EHAM':'4164'}
	timezone = {'Z':8,'Y':10,'C':-7,'K':-7,'KJFK':-4,'E':2}
	today = time.gmtime()

	if airport != 'KJFK':
		timeinterval = timezone[airport[0]]
	else:
		timeinterval = timezone[airport]

	#将输入的时间t和现在的时间ttoday都转换成datetime形式，方便加减：
	if t < today[3]:
		t = datetime.datetime(today[0],today[1],today[2],t) + datetime.timedelta(days = 1)
	else:
		t = datetime.datetime(today[0],today[1],today[2],t)
	ttoday = datetime.datetime(today[0],today[1],today[2],today[3])

	if (t-ttoday).seconds/3600 < 8:
		hour = ttoday + datetime.timedelta(hours = timeinterval)
		hour = hour.hour
	elif 8<=(t-ttoday).seconds/3600<16:
		hour = ttoday + datetime.timedelta(hours = timeinterval)
		hour = hour.hour + 8
	elif 16<=(t-ttoday).seconds/3600<24:
		hour = ttoday + datetime.timedelta(hours = timeinterval)
		hour = hour.hour + 16

	url = 'https://www.accuweather.com/en/cn/' + airport + '/' + aircode[airport] +\
			'_poi/hourly-weather-forecast/' + aircode[airport] + '_poi?hour=' + str(hour)
	headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.2; WOW64; rv:22.0) Gecko/20100101 Firefox/22.0'}

	print url
	request = urllib2.Request(url=url, headers = headers)
	response = urllib2.urlopen(request, timeout=30)
	result = response.read()

	html = BeautifulSoup(result,'lxml')
	table = html.find('table')
	tr = table.find_all('tr')

	timelist = []
	temp = []
	 
	for item in tr[0].find_all('td'):
		timelist.append(item.find('div').get_text())

	for i in range(len(timelist)):
		if 'pm' in timelist[i]:
			if '12' in timelist[i]:
				timelist[i] = int(timelist[i][:2])
			else:
				timelist[i] = int(timelist[i][:timelist[i].find('pm')]) + 12
		else:
			if '12' in timelist[i]:
				timelist[i] = 0
			else:
				timelist[i] = int(timelist[i][:timelist[i].find('am')])

	for item in tr[2].find_all('td'):
		temp.append(item.find('span').get_text())

	#将传入的t转化为各个地方的当地时间
	t = t + datetime.timedelta(hours = timeinterval)

	#判断温度单位，将华氏度转换为摄氏度
	unit = tr[2].find('th').get_text()
	if 'C' in unit:
		indextemp = temp[timelist.index(t.hour)].find('°')
		return temp[timelist.index(t.hour)][:indextemp]
	elif 'F' in unit:
		indextemp = temp[timelist.index(t.hour)].find('°')
		#华氏度换算过程中向上取整，保证安全裕度
		return str(int(math.ceil((int(temp[timelist.index(t.hour)][:indextemp])-32)/1.8)))
	else:
		return -99999