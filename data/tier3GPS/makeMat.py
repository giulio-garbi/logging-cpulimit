import scipy
from scipy.io import savemat
import numpy as np

def readCSV(fname, outparts, rowid):
	entries = {'Client-main':0, 'srv1-service':1, 'srv2-service':2, 'srv3-service':3}
	with open(fname) as f:
		for line in f:
			parts = line.strip().split("; ")
			if parts[0] == 'response time' and parts[2] in entries:
				outparts['RTm'][rowid, entries[parts[2]]] = float(parts[3])
			elif parts[0] == 'throughput' and parts[2] in entries:
				outparts['Tm'][rowid, entries[parts[2]]] = float(parts[3])

with open('whatif_same_concur/allcases.txt') as f:
	lines = [line.strip() for line in f if len(line.strip())>0]
	N = len(lines)
	outparts = {'RTm':np.zeros([N,4], dtype='float'), 'Tm':np.zeros([N,4], dtype='float'), \
		'NC':np.zeros([N,2], dtype='float'), 'Cli':np.zeros([N,1], dtype='float'), \
		'entryNames':np.asarray(['client', 'srv1', 'srv2', 'srv3'], dtype='object')}

	for i in range(N):
		line = lines[i].split()
		Cli = float(line[0])
		NC = float(line[1])
		outparts['Cli'][i,0] = Cli
		outparts['NC'][i,0] = float('inf')
		outparts['NC'][i,1] = NC
		csvfn = line[10]
		readCSV(csvfn, outparts, i)
	savemat('whatif_same_concur/tier3_whatif_same_concur.mat', outparts)