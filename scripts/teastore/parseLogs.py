from batchmeans import MsLog, LogLine
import re


def parseAccessLogValve(msName, logs, ignoreBeforeS):
	ml = MsLog(msName)
	for log in logs:
		for line in log.splitlines():
			mtc = re.search(br'end_ms:(?P<end_ms>\d+) rt_usec:(?P<rt_usec>\d+) code:.+ req:"(?P<req>.+)"', line)
			if mtc is not None:
				exitTimeS = int(mtc.group('end_ms'))/1000.0
				if exitTimeS > ignoreBeforeS:
					#print(exitTimeS)
					rtS = int(mtc.group('rt_usec'))/1000000.0
					endpoint = (mtc.group('req').replace(b" ",b"_")).decode('utf-8')
					#print(exitTimeS, rtS, len(endpoint))
					ml.addLine(LogLine(endpoint, exitTimeS, rtS))
			else:
				print("Invalid log line:", line)
	return ml