import docker
import tarfile
from io import BytesIO
import re
from urllib.request import urlopen
import time
from multiprocessing import *
import sys
from numpy import random
import subprocess

def start_system(jar_path, basePort):
	port = {'vbs':basePort}
	proc = {'vbs': subprocess.Popen(["java", "-Xint", "-jar", jar_path, str(basePort), "2000000"])}
	time.sleep(5)
	return {'port':port, 'proc':proc}

def stop_system(proc):
	msnames = 'vbs'.split()
	for m in msnames:
		proc[m].kill()

def run_case(Cli, WebuiCpu, mf, monitoringSleep, port):
	#change_cpu_quota("webui", WebuiCpu)
	timeIn = time.time_ns()
	allLines = Queue()
	statsOut = Queue()
	wlquit = Queue()
	lastDockerScan = Queue()
	profiling = Value('i', 0)
	isCliOk = Value('i', 0)
	pWload = [Process(target=workload, args=(profiling, isCliOk, allLines, 0.05, wlquit, timeIn+i, port)) for i in range(Cli)]
	time.sleep(320)

def workload(profiling, isCliOk, allLines, sleepTimeS, wlquit, seed, port):
	rnd = random.default_rng(seed)
	rqCnt = 0
	while profiling.value != 0 or isCliOk.value == 0:
		startTimeNs = time.time_ns()
		slTime = sleepTimeS*rnd.exponential(scale=1)
		time.sleep(slTime)

		reqInTimeNs = time.time_ns()
		with urlopen("http://127.0.0.1:"+str(port['vbs'])+"/", timeout=9999999) as response:
			response_content = response.read()
		reqOutTimeNs = time.time_ns()
		#loglineSrv = str(makeLogLine("GET_/tools.descartes.teastore.webui/_HTTP/1.1", reqInTimeNs, reqOutTimeNs))

		rqCnt+=1
		exitTimeNs = time.time_ns()
	allLines.put("stop")
	print("wlexit", rqCnt)
	wlquit.put("x")

if __name__ == '__main__':
	set_start_method("spawn")
	system = start_system('vbs.jar', 9000)
	time.sleep(10)
	for i in [int(k) for k in sys.argv[1:]]:
		monTime = 10.0
		print("Running case",i)
		run_case(i, 1.0, None, monTime, system['port'])
		time.sleep(5)
	print("end_of_tests")
	stop_system(system['proc'])
	sys.exit()