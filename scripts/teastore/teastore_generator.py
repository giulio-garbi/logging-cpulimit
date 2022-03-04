import docker
import tarfile
from io import BytesIO
import re
from parseLogs import parseAccessLogValve
from batchmeans import *
from urllib.request import urlopen
import time
from multiprocessing import *
from matfile import *

def get_logs(client, container):
	logsTxt = []
	for c in client.containers.list(filters={'ancestor':'giuliogarbi/teastore-'+container}):
		bits, stat = c.get_archive("/usr/local/tomcat/logs")
		with BytesIO() as f:
			for chunk in bits:
				f.write(chunk)
			f.seek(0)
			with tarfile.open(fileobj=f, mode='r') as tf:
				logfiles = [fname for fname in tf.getnames() if re.match(r'logs/localhost_access_log[.].+[.]txt', fname)]
				for fname in logfiles:
					with tf.extractfile(fname) as logfile:
						logsTxt.append((logfile.read()))
	return logsTxt

def change_cpu_quota(container, NC):
	client = docker.from_env()
	cpu_period = 1000000
	cpu_quota = int(cpu_period*NC)
	for c in client.containers.list(filters={'ancestor':'giuliogarbi/teastore-'+container}):
		print("X")
		c.update(cpu_period=cpu_period, cpu_quota=cpu_quota)

def run_case(Cli, WebuiCpu, mf):
	change_cpu_quota("webui", WebuiCpu)
	timeIn = time.time_ns()
	allLines = Queue()
	statsOut = Queue()
	wlquit = Queue()
	profiling = Value('i', 1)
	isCliOk = Value('i', 0)
	pMonitor = Process(target=monitorDocker, args=(profiling, 10.0, statsOut, timeIn/1000000000.0, wlquit))
	pMCli = Process(target=monitorCli, args=(isCliOk, allLines, statsOut, wlquit))
	pWload = [Process(target=workload, args=(profiling, isCliOk, allLines, 0.05, wlquit)) for i in range(Cli)]
	for p in pWload:
		p.start()
	pMCli.start()
	pMonitor.start()
	wlquit.get() #pMonitor.join()
	wlquit.get() #pMCli.join()
	for p in pWload:
		wlquit.get()
	timeOut = time.time_ns()
	finalStatsTxt = statsOut.get()+statsOut.get()
	finalStats = MsStats.fromString(finalStatsTxt)
	mf.addSample(finalStats, Cli, {'webui':WebuiCpu}, (timeOut-timeIn)/1000000000.0)

def monitorDocker(profiling, profilingSleepS, statsOut, ignoreBeforeS):
	client = docker.from_env()
	while True:
		time.sleep(profilingSleepS)
		log_consumer = MsLogConsumer(30)
		webui_logs_txt = get_logs(client, 'webui')
		webui_log = parseAccessLogValve('webui', webui_logs_txt, ignoreBeforeS)
		log_consumer.addMsLog(webui_log)
		stats = log_consumer.computeStats()
		if stats.contains('webui-GET_/tools.descartes.teastore.webui/_HTTP/1.1') and stats.isAcceptable(30, 0.1):
			print("quit docker")
			profiling.value = 0
			statsOut.put(str(stats))
			wlquit.put("x")
			return

def monitorCli(isCliOk, allLines, statsOut):
	ml = MsLog("Client")
	while True:
		log_consumer = MsLogConsumer(30)
		lntxt = allLines.get()
		logline = LogLine.fromString(lntxt)
		ml.addLine(logline)
		log_consumer.addMsLog(ml)
		stats = log_consumer.computeStats()
		if stats.isAcceptable(30, 0.1):
			print("quit cli")
			isCliOk.value = 1
			statsOut.put(str(stats))
			wlquit.put("x")
			return

def workload(profiling, isCliOk, allLines, sleepTimeS, wlquit):
	while profiling.value != 0 or isCliOk.value == 0:
		startTimeNs = time.time_ns()
		time.sleep(sleepTimeS)
		with urlopen("http://127.0.0.1:8080/tools.descartes.teastore.webui/") as response:
			response_content = response.read()
		exitTimeNs = time.time_ns()
		exitTimeS = exitTimeNs/1000000000.0
		rtS = (exitTimeNs-startTimeNs)/1000000000.0
		logline = str(LogLine("main", exitTimeS, rtS))
		allLines.put(logline)
	print("wlexit")
	wlquit.put("x")

if __name__ == '__main__':
	mf = Matfile()
	for i in [1]+[k*2 for k in range(1,15)]:
		print("Running case",i)
		run_case(i, 1.0, mf)
		mf.saveMat('../../data/teastore/out.mat')
		time.sleep(5)