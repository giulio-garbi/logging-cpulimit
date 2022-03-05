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
import sys
from numpy import random

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
	cpu_period = 10000
	cpu_quota = int(cpu_period*NC)
	for c in client.containers.list(filters={'ancestor':'giuliogarbi/teastore-'+container}):
		print("X")
		c.update(cpu_period=cpu_period, cpu_quota=cpu_quota)

def run_case(Cli, WebuiCpu, mf, monitoringSleep):
	change_cpu_quota("webui", WebuiCpu)
	timeIn = time.time_ns()
	allLines = Queue()
	statsOut = Queue()
	wlquit = Queue()
	lastDockerScan = Queue()
	profiling = Value('i', 1)
	isCliOk = Value('i', 0)
	pMonitor = Process(target=monitorDocker, args=(profiling, isCliOk, monitoringSleep, statsOut, timeIn/1000000000.0, wlquit, lastDockerScan))
	pMCli = Process(target=monitorCli, args=(profiling, isCliOk, allLines, statsOut, wlquit, Cli, lastDockerScan))
	pWload = [Process(target=workload, args=(profiling, isCliOk, allLines, 0.05, wlquit, timeIn+i)) for i in range(Cli)]
	for p in pWload:
		p.start()
	pMCli.start()
	pMonitor.start()
	wlquit.get() #pMonitor.join()
	wlquit.get() #pMCli.join()
	for p in pWload:
		wlquit.get() #p.join()
	timeOut = time.time_ns()
	finalStatsTxt = statsOut.get()+statsOut.get()
	finalStats = MsStats.fromString(finalStatsTxt)
	pMonitor.kill()
	print("pMonitor terminated")
	pMCli.kill()
	print("pMCli terminated")
	cnt = 0
	for p in pWload:
		p.kill()
		print("pWload["+str(cnt)+"] terminated")
		cnt += 1
	mf.addSample(finalStats, Cli, {'webui':WebuiCpu}, (timeOut-timeIn)/1000000000.0)

def monitorDocker(profiling, isCliOk, profilingSleepS, statsOut, ignoreBeforeS, wlquit, lastDockerScan):
	client = docker.from_env()
	pOk = False
	while profiling.value != 0 or isCliOk.value == 0:
		time.sleep(profilingSleepS)
		log_consumer = MsLogConsumer(30)
		webui_logs_txt = get_logs(client, 'webui')
		webui_log = parseAccessLogValve('webui', webui_logs_txt, ignoreBeforeS)
		log_consumer.addMsLog(webui_log)
		stats = log_consumer.computeStats()
		if not pOk and stats.contains('webui-GET_/tools.descartes.teastore.webui/_HTTP/1.1') and stats.isAcceptable(30, 0.1):
			print("docker satisfied")
			profiling.value = 0
			pOk = True

	lastDockerScan.get()
	log_consumer = MsLogConsumer(30)
	webui_logs_txt = get_logs(client, 'webui')
	webui_log = parseAccessLogValve('webui', webui_logs_txt, ignoreBeforeS)
	log_consumer.addMsLog(webui_log)
	stats = log_consumer.computeStats()
	statsOut.put(str(stats))
	wlquit.put("x")

def monitorCli(profiling, isCliOk, allLines, statsOut, wlquit, nWorkers, lastDockerScan):
	ml = MsLog("Client")
	clOk = False
	lnCnt = 0
	workersEnded = 0
	while (profiling.value != 0 or isCliOk.value == 0) and workersEnded < nWorkers:
		log_consumer = MsLogConsumer(30)
		lntxt = allLines.get()
		if lntxt == "stop":
			workersEnded += 1
		else:
			logline = LogLine.fromString(lntxt)
			ml.addLine(logline)
			lnCnt+=1
			log_consumer.addMsLog(ml)
			stats = log_consumer.computeStats()
			if not clOk and stats.isAcceptable(30, 0.1):
				print("cli satisfied")
				clOk = True
				isCliOk.value = 1

	while workersEnded < nWorkers:
		lntxt = allLines.get()
		if lntxt == "stop":
			workersEnded += 1
		else:
			logline = LogLine.fromString(lntxt)
			ml.addLine(logline)
			lnCnt+=1

	last_log_consumer = MsLogConsumer(30)
	last_log_consumer.addMsLog(ml)
	stats = last_log_consumer.computeStats()
	statsOut.put(str(stats))
	print("cli processing ended", lnCnt)
	lastDockerScan.put("x")
	wlquit.put("x")

def workload(profiling, isCliOk, allLines, sleepTimeS, wlquit, seed):
	rnd = random.default_rng(seed)
	rqCnt = 0
	while profiling.value != 0 or isCliOk.value == 0:
		startTimeNs = time.time_ns()
		slTime = sleepTimeS*rnd.exponential(scale=1)
		time.sleep(slTime)
		with urlopen("http://127.0.0.1:8080/tools.descartes.teastore.webui/", timeout=9999999) as response:
			response_content = response.read()
		rqCnt+=1
		exitTimeNs = time.time_ns()
		exitTimeS = exitTimeNs/1000000000.0
		rtS = (exitTimeNs-startTimeNs)/1000000000.0
		logline = str(LogLine("main", exitTimeS, rtS))
		allLines.put(logline)
	allLines.put("stop")
	print("wlexit", rqCnt)
	wlquit.put("x")

if __name__ == '__main__':
	set_start_method("spawn")
	mf = Matfile()
	for i in [int(k) for k in sys.argv[1:]]:
		monTime = 320.0
		print("Running case",i)
		run_case(i, 1.0, mf, monTime)
		mf.saveMat('../../data/teastore/out.mat')
		time.sleep(5)
	print("end_of_tests")
	sys.exit()