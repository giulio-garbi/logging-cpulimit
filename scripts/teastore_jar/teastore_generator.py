import docker
import tarfile
from io import BytesIO
import re
from parseLogs import parseMsLogs
from batchmeans import *
from urllib.request import urlopen
import time
from multiprocessing import *
from matfile import *
import sys
from numpy import random
import subprocess

def start_system(jar_path, basePort):
	msnames = 'web recommender persistence image auth'.split()
	port = {'registry': basePort}
	proc = {'registry': subprocess.Popen(["java", "-Djava.compiler=NONE", "-jar", jar_path, "registry", str(port['registry'])])}
	reg_uri = "http://127.0.0.1:"+str(port['registry'])
	time.sleep(5)
	for i in range(len(msnames)):
		port[msnames[i]] = basePort+i+1
		proc[msnames[i]] = subprocess.Popen(["java", "-Djava.compiler=NONE", "-jar", jar_path, msnames[i], reg_uri, str(port[msnames[i]])])
	return {'port':port, 'proc':proc}

def stop_system(proc):
	msnames = 'web recommender persistence image auth registry'.split()
	for m in msnames:
		proc[m].kill()

def get_logs(port):
	with urlopen("http://127.0.0.1:"+str(port['registry'])+"/log/", timeout=9999999) as response:
		response_content = response.read()
		return response_content

def change_cpu_quota(container, NC):
	client = docker.from_env()
	cpu_period = 10000
	cpu_quota = int(cpu_period*NC)
	for c in client.containers.list(filters={'ancestor':'giuliogarbi/teastore-'+container}):
		print("X")
		c.update(cpu_period=cpu_period, cpu_quota=cpu_quota)

def run_case(Cli, WebuiCpu, mf, monitoringSleep, port):
	#change_cpu_quota("webui", WebuiCpu)
	timeIn = time.time_ns()
	allLines = Queue()
	statsOut = Queue()
	wlquit = Queue()
	lastDockerScan = Queue()
	profiling = Value('i', 0)
	isCliOk = Value('i', 0)
	pMonitor = Process(target=monitorMsLog, args=(profiling, isCliOk, monitoringSleep, statsOut, timeIn/1000000000.0, wlquit, lastDockerScan, port))
	pMCli = Process(target=monitorCli, args=(profiling, isCliOk, allLines, statsOut, wlquit, Cli, lastDockerScan))
	pWload = [Process(target=workload, args=(profiling, isCliOk, allLines, 0.05, wlquit, timeIn+i, port)) for i in range(Cli)]
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

def monitorMsLog(profiling, isCliOk, profilingSleepS, statsOut, ignoreBeforeS, wlquit, lastMsScan, port):
	logsmap = dict()
	pOk = False
	while profiling.value != 0 or isCliOk.value == 0:
		log_consumer = MsLogConsumer(30, 0.1)
		time.sleep(profilingSleepS)
		logs_txt = get_logs(port)
		logsmap = parseMsLogs(logs_txt, ignoreBeforeS, logsmap)
		for log in logsmap.values():
			log_consumer.addMsLog(log)
		stats = log_consumer.computeStats(99999999999)
		print(str(stats))
		if not pOk and stats.isAcceptable(30, 0.05, 0.1):
			print("docker satisfied")
			profiling.value = 0
			pOk = True

	lastMsScan.get()
	log_consumer = MsLogConsumer(30, 0.1)
	logs_txt = get_logs(port)
	logsmap = parseMsLogs(logs_txt, ignoreBeforeS, logsmap)
	for log in logsmap.values():
		log_consumer.addMsLog(log)
	stats = log_consumer.computeStats(99999999999)
	statsOut.put(str(stats))
	wlquit.put("x")

def monitorCli(profiling, isCliOk, allLines, statsOut, wlquit, nWorkers, lastDockerScan):
	ml = MsLog("Client")
	clOk = False
	lnCnt = 0
	workersEnded = 0
	DBGstartTimeS = time.time()
	itr = 0
	while (profiling.value != 0 or isCliOk.value == 0) and workersEnded < nWorkers:
		itr+=1
		log_consumer = MsLogConsumer(30, 0.1)
		lntxt = allLines.get()
		if lntxt == "stop":
			workersEnded += 1
		else:
			logline = LogLine.fromString(lntxt)
			ml.addLine(logline)
			lnCnt+=1
			log_consumer.addMsLog(ml)
			stats = log_consumer.computeStats(99999999999)
			if itr % 1000 == 0:
				print("nCli; "+str(nWorkers)+"\n"+str(stats))
			if time.time() >= DBGstartTimeS+320 not clOk and stats.isAcceptable(30, 0.05, 0.1):
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

	last_log_consumer = MsLogConsumer(30, 0.1)
	last_log_consumer.addMsLog(ml)
	stats = last_log_consumer.computeStats(99999999999)
	statsOut.put(str(stats))
	print("cli processing ended", lnCnt)
	lastDockerScan.put("x")
	wlquit.put("x")

def makeLogLine(req, startTimeNs, exitTimeNs):
	exitTimeS = exitTimeNs/1000000000.0
	rtS = (exitTimeNs-startTimeNs)/1000000000.0
	return LogLine(req, exitTimeS, rtS)

def workload(profiling, isCliOk, allLines, sleepTimeS, wlquit, seed, port):
	rnd = random.default_rng(seed)
	rqCnt = 0
	while profiling.value != 0 or isCliOk.value == 0:
		startTimeNs = time.time_ns()
		slTime = sleepTimeS*rnd.exponential(scale=1)
		time.sleep(slTime)

		reqInTimeNs = time.time_ns()
		with urlopen("http://127.0.0.1:"+str(port['web'])+"/index/", timeout=9999999) as response:
			response_content = response.read()
		reqOutTimeNs = time.time_ns()
		#loglineSrv = str(makeLogLine("GET_/tools.descartes.teastore.webui/_HTTP/1.1", reqInTimeNs, reqOutTimeNs))

		rqCnt+=1
		exitTimeNs = time.time_ns()
		logline = str(makeLogLine("main", startTimeNs, exitTimeNs))
		allLines.put(logline)
		#allLines.put(loglineSrv)
	allLines.put("stop")
	print("wlexit", rqCnt)
	wlquit.put("x")

if __name__ == '__main__':
	set_start_method("spawn")
	system = start_system('TeaStoreMongo-0.0.1-SNAPSHOT-jar-with-dependencies.jar', 9000)
	time.sleep(10)
	mf = Matfile()
	for i in [int(k) for k in sys.argv[1:]]:
		monTime = 10.0
		print("Running case",i)
		run_case(i, 1.0, mf, monTime, system['port'])
		mf.saveMat('../../data/teastore_jar/out.mat')
		time.sleep(5)
	print("end_of_tests")
	stop_system(system['proc'])
	sys.exit()