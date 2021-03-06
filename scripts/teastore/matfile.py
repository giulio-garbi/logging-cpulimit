import scipy
from scipy.io import savemat
import numpy as np

class Matfile:
	def __init__(self):
		self.entryNamesSet = set()
		self.msSet = set()
		self.CliList = []
		self.NCmapList = []
		self.statsList = []
		self.profTimeList = []

	def addSample(self, stats, Clis, NCmap, profilingTimeS):
		self.statsList.append(stats)
		self.CliList.append([Clis])
		self.profTimeList.append([profilingTimeS])
		self.NCmapList.append(NCmap)
		for msName in NCmap:
			self.msSet.add(msName)
		for label in stats.rtMean:
			if label != 'Client-main':
				self.entryNamesSet.add(label)

	def saveMat(self, fname):
		outdata = dict()

		taskNamesL = list(self.msSet)
		taskNamesL.sort()
		taskNamesL = ['Client']+taskNamesL
		taskNames = np.array(taskNamesL, dtype="object")

		entryNamesL = list(self.entryNamesSet)
		entryNamesL.sort()
		entryNamesL = ['Client-main']+entryNamesL
		entryNames = np.array(entryNamesL, dtype="object")

		Cli = np.array(self.CliList, dtype="float")

		profTime = np.array(self.profTimeList, dtype="float")

		NCList = [[float('inf')]+[NCmap[t] for t in taskNamesL[1:]] for NCmap in self.NCmapList]
		NC = np.array(NCList, dtype="float")

		RTmL = [[stats.rtMean[e] for e in entryNamesL] for stats in self.statsList]
		RTm = np.array(RTmL, dtype="float")
		RTmCIL = [[stats.rtCI[e] for e in entryNamesL] for stats in self.statsList]
		RTmCI = np.array(RTmCIL, dtype="float")

		TmL = [[stats.thrMean[e] for e in entryNamesL] for stats in self.statsList]
		Tm = np.array(TmL, dtype="float")
		TmCIL = [[stats.thrCI[e] for e in entryNamesL] for stats in self.statsList]
		TmCI = np.array(TmCIL, dtype="float")

		NsL = [[stats.nrSamples[e] for e in entryNamesL] for stats in self.statsList]
		Ns = np.array(NsL, dtype="float")

		outdata['taskNames'] = taskNames
		outdata['entryNames'] = entryNames
		outdata['Cli'] = Cli
		outdata['NC'] = NC
		outdata['RTm'] = RTm
		outdata['Tm'] = Tm
		outdata['RTmCI'] = RTmCI
		outdata['TmCI'] = TmCI
		outdata['profTime'] = profTime
		outdata['Ns'] = Ns

		savemat(fname, outdata)