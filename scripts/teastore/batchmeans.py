import numpy as np

class MsLog:
    def __init__(self, name):
        self.name = name
        self.lines = dict()

    def addLine(self, line):
        if line.endpoint not in self.lines:
            self.lines[line.endpoint] = []
        self.lines[line.endpoint].append(line)

class LogLine:
    def __init__(self, endpoint, exitTimeS, rtS):
        self.endpoint = endpoint
        self.exitTimeS = float(exitTimeS)
        self.rtS = float(rtS)

class MsStats:
    def __init__(self):
        self.rtCI = dict()
        self.rtMean = dict()
        self.rtBatchesNum = dict()
        self.thrMean = dict()

    def isAcceptable(self, N, rtAbsError):
        return all([abs(self.rtCI[label][0]-self.rtMean[label]) <= rtAbsError and \
            self.rtBatchesNum[label] >= N and \
            self.thrMean[label] is not None for label in self.rtCI])

    

class MsLogConsumer:
    def __init__(self, K):
        #size of batches
        self.K = K

        #endpoint indexes
        self.epIdxs = dict()

        #response time batches
        self.rtBatches = []
        #response time counters
        self.rtSamples = []

        #time between exits sums
        self.dtExitSums = []
        #time between exits counters
        self.dtExitSamples = []

    def addMsLog(self, mslog):
        for ep in mslog.lines:
            label = mslog.name+"-"+ep
            if label not in self.epIdxs:
                epIdx = len(self.epIdxs)
                self.epIdxs[label] = epIdx

                self.rtBatches.append
            else:
                epIdx = self.epIdxs[label]

            log = mslog.lines[ep]
            rtS = [ll.rtS for ll in log]

            # adding the observed response times into the batches, ensuring that each batch is long at most K
            startFrom = 0

            if self.rtSamples[epIdx]%self.K > 0: # if some batch is not full
                toAdd = self.K-(self.rtSamples[epIdx]%self.K)
                self.rtBatches[epIdx][-1] += rtS[startFrom:startFrom+toAdd]
                startFrom = startFrom+toAdd

            # add new batches as needed (last one might not be full)
            for i in range(startFrom, len(rtS), self.K):
                self.rtBatches[epIdx].append(rtS[i:i+self.K])

            # count the new samples
            self.rtSamples[epIdx] += len(rtS)

            # processing the new time between exits. No batch means needed here, just the average
            exitS = [ll.exitTimeS for ll in log]
            exitS.sort()
            if len(exitS) > 1:
                self.dtExitSums[epIdx] += exitS[-1]-exitS[0]
                self.dtExitSamples[epIdx] += len(exitS)-1

    def computeStats(self):
        stats = MsStats()
        for label in self.epIdxs:
            epIdx = self.epIdxs[label]
            rtMeans = np.mean(np.array(self.rtBatches[epIdx][0:self.rtSamples[epIdx]//self.K]), axis=1)
            CI = st.t.interval(0.99, len(rtMeans[1:]) - 1, loc=np.mean(rtMeans[1:]), scale=st.sem(rtMeans[1:]))
            stats.rtCI[label] = CI
            stats.rtMean[label] = np.mean(rtMeans[1:])
            stats.rtBatchesNum[label] = self.rtSamples[epIdx]//self.K
            stats.thrMean[label] = self.dtExitSamples[epIdx]/self.dtExitSums[epIdx]