import scipy
from scipy.io import savemat
import numpy as np
import sys

def readCSV(fname, outparts, rowid):
	entries = {'Client-main':0, 'srv1-service':1, 'srv2-service':2, 'srv3-service':3}
	with open(fname) as f:
		for line in f:
			parts = line.strip().split("; ")
			if parts[0] == 'response time' and parts[2] in entries:
				outparts['RTm'][rowid, entries[parts[2]]] = float(parts[3])
			elif parts[0] == 'throughput' and parts[2] in entries:
				outparts['Tm'][rowid, entries[parts[2]]] = float(parts[3])
			elif parts[0] == 'cli':
				outparts['Cli'][i,0] = float(parts[3])

if len(sys.argv)<3:
	print("Usage: <out.mat> <file1-NC.csv>, <file2-NC.csv> ... <fileN-NC.csv>")
else:
	outfn = sys.argv[1]
	infns = sys.argv[2:]

	N = len(infns)
	outparts = {'RTm':np.zeros([N,4], dtype='float'), 'Tm':np.zeros([N,4], dtype='float'), \
		'NC':np.zeros([N,2], dtype='float'), 'Cli':np.zeros([N,1], dtype='float'), \
		'entryNames':np.asarray(['client', 'srv1', 'srv2', 'srv3'], dtype='object')}

	for i in range(N):
		NC = float(infns[i].split("-")[-1].rsplit('.', 1)[0])
		outparts['Cli'][i,0] = float('NaN')
		outparts['NC'][i,0] = float('inf')
		outparts['NC'][i,1] = NC
		csvfn = infns[i]
		readCSV(csvfn, outparts, i)
	savemat(outfn, outparts)