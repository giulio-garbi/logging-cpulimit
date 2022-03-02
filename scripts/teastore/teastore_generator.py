import docker
import tarfile
from io import BytesIO
import re
from parseLogs import parseAccessLogValve
from batchmeans import *
from urllib.request import urlopen
import time
from multiprocessing import *

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

def rm_logs(client, container):
	pass

def run_case(Cli, WebuiCpu):
	pass

def monitor(output, profilingSleepS):
	client = docker.from_env()
	while True:
		print("wait")
		time.sleep(profilingSleepS)
		log_consumer = MsLogConsumer(30)
		webui_logs_txt = get_logs(client, 'webui')
		webui_log = parseAccessLogValve('webui', webui_logs_txt)
		log_consumer.addMsLog(webui_log)
		stats = log_consumer.computeStats()
		stats.dump()
		if stats.isAcceptable(30, 0.1):
			print("quit")
			#output.put("ans")
			return

def workload(profiling, allLines, sleepTimeS):
	loglines = []
	while profiling.value != 0:
		startTimeNs = time.time_ns()
		time.sleep(sleepTimeS)
		with urlopen("http://127.0.0.1:8080/tools.descartes.teastore.webui/") as response:
			response_content = response.read()
		exitTimeNs = time.time_ns()
		exitTimeS = exitTimeNs/1000000000.0
		rtS = (exitTimeNs-startTimeNs)/1000000000.0
		loglines.append(LogLine("main", exitTimeS, rtS))
	#allLines.put(loglines)

if __name__ == '__main__':
	Cli = 1
	# TODO RM LOGS
	allLines = Queue()
	profiling = Value('i', 1)
	isCliOk = Array('i', [0]*Cli)
	pMonitor = Process(target=monitor, args=(None, 10.0))
	pWload = [Process(target=workload, args=(profiling, allLines, 0.1)) for i in range(Cli)]
	for p in pWload:
		p.start()
	pMonitor.start()
	pMonitor.join()
	profiling.value = 0
	for p in pWload:
		p.join()

#client = docker.from_env()
#webui_logs_txt = get_logs(client, 'webui')
#webui_log = parseAccessLogValve('webui', webui_logs_txt)
#
#log_consumer = MsLogConsumer(30)
#log_consumer.addMsLog(webui_log)
#log_consumer.computeStats()