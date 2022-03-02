from batchmeans import MsLog, LogLine
import re


def parseAccessLogValve(msName, logs):
	ml = MsLog(msName)
	for log in logs:
		for line in log.splitlines():
			mtc = re.search('end_ms:(?P<end_ms>\\d+) rt_usec:(?P<rt_usec>\\d+) req:"(?P<req>.+)"', line)
			if mtc is not None:
				exitTimeS = int(mtc.group('end_ms'))/1000.0
				rtS = int(mtc.group('rt_usec'))/1000000.0
				endpoint = mtc.group('req').replace(" ","_")
				ml.addLine(LogLine(endpoint, exitTimeS, rtS))
	return ml