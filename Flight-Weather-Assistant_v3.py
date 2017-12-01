# -*- coding: UTF-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf8')

import sys
import traceback
from collections import OrderedDict
from PyQt4 import QtCore, QtGui, uic

import category_v3 as cat
import re

# qtCreatorFile = "D:\python\myfiles\\continental\\continental_v2.ui" # Enter file here.
qtCreatorFile = "continental_v3.ui" # Enter file here.

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class MyApp(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)

        self.abstract_but.clicked.connect(self.abstract_flight_info)
        self.run_but.clicked.connect(self.run_continent)

    def abstract_flight_info(self):
    	#读入航班信息：
    	f = open('flight_information.txt','r')
    	flight_info = {}
    	for line in f.readlines():
    		flight_info[int(line.split()[0])] = line.split(' ',1)[1].split()
    	flight_num = int(self.flight_num.text())

    	#如无匹配航班，则弹出告警框：
    	if not flight_info.has_key(flight_num):
    		QtGui.QMessageBox.information(self, 'Warning',unicode('没有这个航班！'))
    		raise ValueError
    	
    	#将航班信息填入对应框中：
    	self.depature_airport.setText(flight_info[flight_num][0])
    	self.depature_t.setText(flight_info[flight_num][1])
    	self.dest_airport.setText(flight_info[flight_num][2])
    	self.dest_t.setText(flight_info[flight_num][3])
    	self.alter_airport_1.setText(flight_info[flight_num][4])
    	self.alter_airport_2.setText(flight_info[flight_num][5])

    #把北京时转换为世界时，并转换成一个时间区间（前1小时，后2小时）：
    def time_convert(self, input_t, flag = 1):
    	if flag == 1:
    		result_t = [input_t-8-1, input_t-8+2, input_t-8]
    	elif flag == 2:
    		result_t = [input_t-8-2, input_t-8+3, input_t-8]

    	for i in range(len(result_t)):
    		if result_t[i] < 0:
    			result_t[i] += 24
    		elif result_t[i] >= 24:
    			result_t[i] -= 24
    		result_t[i] = str(result_t[i]).zfill(2)+':00Z'
    	return result_t[:2], int(result_t[2][:2])

    def run_continent(self):

		#读入机场和时间数据
		t = OrderedDict()
		t[str(self.depature_airport.text())] = self.time_convert(int(self.depature_t.text()))[0]
		t[str(self.dest_airport.text())] = self.time_convert(int(self.dest_t.text()))[0]

		plantext = str(self.time_window.toPlainText())
		#如忘记粘贴时间窗口码，则弹出告警框：
		if plantext == '':
			QtGui.QMessageBox.information(self, 'Warning',unicode('又忘了把时间窗口码粘过来了吧！'))
			raise ValueError

		for item in plantext.split('\n'):
			if item.split()[0].strip() == str(self.depature_airport.text()):
				t[str(self.depature_airport.text())] = [t[str(self.depature_airport.text())][0],item.split()[5]]
			elif item.split()[0].strip() == str(self.dest_airport.text()):
				t[str(self.dest_airport.text())] = [item.split()[3],t[str(self.dest_airport.text())][1]]
			else:
				t[item.split()[0].strip()] = [item.split()[3], item.split()[5]]

		if t.has_key(str(self.alter_airport_1.text())):
			t[str(self.alter_airport_1.text())] = [t[str(self.alter_airport_1.text())][0], self.time_convert(int(self.dest_t.text()), 2)[0][1]]
		else:
			t[str(self.alter_airport_1.text())] = self.time_convert(int(self.dest_t.text()), 2)[0]
		if t.has_key(str(self.alter_airport_2.text())):
			t[str(self.alter_airport_2.text())] = [t[str(self.alter_airport_2.text())][0], self.time_convert(int(self.dest_t.text()), 2)[0][1]]
		else:
			t[str(self.alter_airport_2.text())] = self.time_convert(int(self.dest_t.text()), 2)[0]
		print t

		#读入天气现象
		f = open('weather.txt','r')
		weathertype = {}
		for item in f.readlines():
			weathertype[item.split()[1]] = item.split()[0].decode('gb2312')
		f.close()

		#逐条处理每个机场：
		i = 0
		textresult = ''
		texttafraw = ''
		for airport, airtime in t.items():
			try:
				print airport, airtime
				result, tafraw = cat.decompose(airport, airtime[0][:2], airtime[1][:2])

				if len(result) > 1:
					#将时段内每个小时的天气状态整理到result[0]中：
					for j in range(1,len(result)):
						for key in result[j].keys():
							#如果天气状态产生变化：
							if result[j][key] != result[0][key]:
								#如果变化前后都不为空，则用‘turn：’衔接：
								if (result[0][key].strip() not in ['','BR','FU','HZ']) and (result[j][key].strip() not in ['','BR','FU','HZ']):
									result[0][key] = result[0][key] + ' turn: ' + result[j][key]
								#如果之前为空，变化后有天气，则用后者取代前者：
								elif (result[0][key].strip() in ['','BR','FU','HZ']):
									result[0][key] = result[j][key]
								#如果之前不为空，变化后为空，则不处理
				print result[0]
				
				#判断天气：
				resultwx = ''
				#去掉重复的天气现象：
				wx = list(set(result[0]['weather'].split()))
				wx.sort(key = result[0]['weather'].split().index)
				while len(wx)>0 and wx[-1] in ['turn:','TEMPO:']:
					wx.pop(-1)

				if 'TEMPO:' in wx and (wx[wx.index('TEMPO:') + 1] in ['BR','HZ','FU','turn:']):
					wx.pop(wx.index('TEMPO:'))

				for item in wx:
					if ('TEMPO' in item):
						resultwx += '短时'
						continue
					if ('PROB30' in item):
						resultwx += '30%概率'
						continue
					if 'turn:' in item:
						resultwx += '转'
						continue
					if ('CAVOK' in item) or ('HZ' in item) or ('BR' in item) or ('FU' in item):
						continue
					resultwx = resultwx + weathertype[item] + '，'
					
				if (resultwx == '短时') or (resultwx == ''):
					resultwx = '晴'

				#当出现两个短时天气时，用‘伴’相连接：
				if resultwx.count('短时') == 2:
					resultwx = unicode(resultwx)
					ind1 = resultwx.find('，', resultwx.find('短时'))
					resultwx = resultwx[:ind1] + '伴' + resultwx[ind1+3:]

				#判断云量：
				resultcld = ''
				if len(result[0]['cloud']) > 1:
					for item in result[0]['cloud'].split():
						if 'OVC' in item:
							resultcld = '阴，'
							break
						if ('BKN' in item) or ('SCT' in item):
							resultcld = '多云，'
							break
						elif ('FEW' in item):
							resultcld = '少云，'

					ceil = cat.find_min(result[0]['cloud'])
					if ceil < 120 and ('VV' in result[0]['cloud']):
						resultcld = resultcld + '短时垂直能见度' + str(ceil) + '-' + str(ceil+30) + '米，'
					elif ceil <120:
						resultcld = resultcld + '关注少量' + str(ceil) + '-' + str(ceil+30) + '米低云，'

				#判断风：
				resultwd = ''
				if len(result[0]['wind'].split()) > 1:
					temp = re.split('TEMPO:|PROB30:|PROB40:', result[0]['wind'])[0].split('turn:')
					if len(temp) > 1:
						# 提取比较参数，有阵风就用阵风比，无阵风就用平均风速比
						mag_compare = []
						for item in temp:
							if 'G' in item:
								mag_compare.append(int(item.strip()[6:8]))
							else:
								mag_compare.append(int(item.strip()[3:5]))

						if mag_compare[0]>=mag_compare[1]:
							winddir, windmag = cat.winddecode(temp[0].strip())
							if 'G' in temp[1] and 'G' in temp[0] and cat.winddecode(temp[1].strip())[1] != cat.winddecode(temp[0].strip())[1]:
								gust = unicode(cat.winddecode(temp[1].strip())[1])
								windmag = unicode(windmag)
								windmag = windmag[:windmag.find('阵风')+2] + gust[gust.find('阵风')+2:gust.find('m',gust.find('阵风'))] + '-' + windmag[windmag.find('阵风')+2:]
						else:
							winddir, windmag = cat.winddecode(temp[1].strip())
							if 'G' in temp[1] and 'G' in temp[0]:
								gust = unicode(cat.winddecode(temp[0].strip())[1])
								windmag = unicode(windmag)
								windmag = windmag[:windmag.find('阵风')+2] + gust[gust.find('阵风')+2:gust.find('m',gust.find('阵风'))] + '-' + windmag[windmag.find('阵风')+2:]
					else:
						winddir, windmag = cat.winddecode(temp[0].strip())
					if windmag == '微风':
						resultwd = windmag
					else:
						resultwd = winddir + windmag

					for item in ['TEMPO:','PROB40:','PROB30:']:
						if item in result[0]['wind'].split():
							if item =='PROB30:':
								conj = '，30%概率短时'
							else:
								conj = '，短时'

							temp = result[0]['wind'].split(item)[1]
							if 'VRB' in temp and cat.winddecode(temp.strip())[1]!='微风':
								winddir, windmag = cat.winddecode(temp.strip())
								resultwd = resultwd + conj+'大' + windmag
							elif cat.winddecode(temp.strip())[1]!='微风':
								winddir, windmag = cat.winddecode(temp.strip())
								resultwd = resultwd + conj + winddir + windmag
				else:
					winddir, windmag = cat.winddecode(result[0]['wind'].strip())
					if windmag == '微风':
						resultwd = windmag
					else:
						resultwd = winddir + windmag
				if ('阵风' in windmag):
					gust = unicode(windmag.split('阵风')[1])
					if ('-' in gust and int(gust[:gust.find('-')])>10) or ('-' not in gust and int(gust[:gust.find('m')])>10):
						resultwd += '，注意风切变' 

				#判断能见度：
				resultvis = ''
				if len(result[0]['vis'])>1:
					vis = cat.find_min(result[0]['vis'])
					#对于起降机场和目的地备降场，标准都按1600米算
					if (i<2 or i>=len(t)-2) and vis < 1600:
						resultvis = '能见度'  + str(vis) + '米左右，'
					#对于ETOPS航路备降场，标准按3300算
					if (i>=2 and i<len(t)-2) and vis < 3300:
						resultvis = '能见度'  + str(vis) + '米左右，'
					#当能见度低于阈值时，且无FZ相关天气时，应提及天气现象中的轻雾、烟等现象
					if len(resultvis) != 0:
						visweath = ['BR','HZ','FU']
						for item in visweath:
							if item in result[0]['weather'] and 'FG' not in result[0]['weather']:
								resultvis = weathertype[item] + '，' + resultvis
					if len(resultvis)!=0:
						if 'TEMPO' in result[0]['vis']:
							resultvis = '短时' + resultvis
						if 'PROB30' in result[0]['vis']:
							resultvis = '30%概率短时' + resultvis

				#整理成最终语句：
				if (resultwx.find('短时') == 0):
					resultsum = resultcld + resultwx + resultvis + resultwd
				elif resultwx == '晴' and resultcld != '':
					if '少云' in resultcld:
						resultsum = resultwx + '到' + resultcld + resultvis + resultwd
					else:
						resultsum = resultcld + resultvis + resultwd
				elif resultwx == '晴' and resultcld == '':
					resultsum = resultwx + '，' + resultvis + resultwd
				elif '垂直' in resultcld:
					resultsum = resultwx + resultcld + resultvis + resultwd
				else:
					resultsum = resultwx + resultvis + resultwd

				resultsum = str(i+1)+'. '+airport+'  '+airtime[0]+' - '+airtime[1]+'  '+resultsum
				tafraw = str(i+1) + '. ' + tafraw + '='

			except Exception as e:
				resultsum = str(i+1)+'. '+airport+'  '+u'！！！报文请求超时'
				tafraw = str(i+1) + '. ' + u'！！！报文请求超时'
				traceback.print_exc()

			#给出起飞落地机场温度：
			try:
				if i == 0:
					resulttemp = cat.temperature(airport, self.time_convert(int(self.depature_t.text()))[1])
					resultsum = resultsum + '，预飞时刻气温约' + resulttemp + '℃'
				if i == 1:
					print i
					resulttemp = cat.temperature(airport, self.time_convert(int(self.dest_t.text()))[1])
					resultsum = resultsum + '，预达时刻气温约' + resulttemp + '℃'
			except Exception as e:
				resultsum = resultsum + '，！！！accuweather请求超时'

			i += 1
			textresult = textresult + resultsum + '。' + '\n'
			texttafraw = texttafraw + tafraw + '\n\n'

		self.result_window.clear()
		self.result_window.insertPlainText(textresult)

		self.result_window_2.clear()
		self.result_window_2.insertPlainText(texttafraw)

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
