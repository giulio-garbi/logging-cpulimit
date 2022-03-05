import numpy as np
import scipy.stats as st

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

    def __str__(self):
        return str(self.exitTimeS)+" "+str(self.rtS)+" "+self.endpoint

    @staticmethod
    def fromString(s):
        parts = s.split(" ",2)
        return LogLine(parts[2], parts[0], parts[1])

class MsStats:
    def __init__(self):
        self.rtCI = dict()
        self.rtMean = dict()
        self.rtBatchesNum = dict()
        self.thrMean = dict()
        self.thrBatchesNum = dict()
        self.thrCI = dict()
        self.nrSamples = dict()

    def isAcceptable(self, N, rtAbsError):
        return all([abs(self.rtCI[label][0]-self.rtMean[label]) <= rtAbsError and \
            self.rtBatchesNum[label] >= N and \
            self.thrMean[label] is not None for label in self.rtCI])

    def contains(self, *labels):
        return all(l in self.rtMean for l in labels)

    def dump(self):
        for label in self.rtCI:
            print(label," rt ",self.rtMean[label],' +/- ',abs(self.rtCI[label][0]-self.rtMean[label]))
            print(label," thr ",self.thrMean[label])

    def __str__(self):
        ans = ""
        for (label,ci) in self.rtCI.items():
            ans+="rtCI "+str(ci[0])+" "+str(ci[1])+" "+label+"\n"
        for (label,m) in self.rtMean.items():
            ans+="rtMean "+str(m)+" "+label+"\n"
        for (label,bn) in self.rtBatchesNum.items():
            ans+="rtBatchesNum "+str(bn)+" "+label+"\n"
        for (label,t) in self.thrMean.items():
            ans+="thrMean "+str(t)+" "+label+"\n"
        for (label,ci) in self.thrCI.items():
            ans+="thrCI "+str(ci[0])+" "+str(ci[1])+" "+label+"\n"
        for (label,bn) in self.thrBatchesNum.items():
            ans+="thrBatchesNum "+str(bn)+" "+label+"\n"
        for (label,t) in self.nrSamples.items():
            ans+="nrSamples "+str(t)+" "+label+"\n"
        return ans

    @staticmethod
    def fromString(s):
        ans = MsStats()
        for line in s.splitlines():
            if len(line)>0:
                parts = line.split()
                if parts[0] == "rtCI":
                    ans.rtCI[parts[3]] = (float(parts[1]),float(parts[2]))
                elif parts[0] == "rtMean":
                    ans.rtMean[parts[2]] = float(parts[1])
                elif parts[0] == "rtBatchesNum":
                    ans.rtBatchesNum[parts[2]] = int(parts[1])
                elif parts[0] == "thrMean":
                    ans.thrMean[parts[2]] = float(parts[1])
                elif parts[0] == "nrSamples":
                    ans.nrSamples[parts[2]] = float(parts[1])
                elif parts[0] == "thrCI":
                    ans.thrCI[parts[3]] = (float(parts[1]),float(parts[2]))
                elif parts[0] == "thrBatchesNum":
                    ans.thrBatchesNum[parts[2]] = int(parts[1])
        return ans
    

class MsLogConsumer:
    def __init__(self, K, thrWindowS):
        #size of batches
        self.K = K

        #endpoint indexes
        self.epIdxs = dict()

        #response time batches
        self.rtBatches = []
        #response time counters
        self.rtSamples = []

        #throughput batches
        self.thrBatches = []
        #throughput counters
        self.thrSamples = []
        #throughput window size
        self.thrWindowS = thrWindowS

        '''
        #time between exits sums
        self.dtExitSums = []
        #time between exits counters
        self.dtExitSamples = []'''

    def addMsLog(self, mslog):
        for ep in mslog.lines:
            label = mslog.name+"-"+ep
            if label not in self.epIdxs:
                epIdx = len(self.epIdxs)
                self.epIdxs[label] = epIdx

                self.rtBatches.append([])
                self.rtSamples.append(0)
                self.thrBatches.append([])
                self.thrSamples.append(0)
                #self.dtExitSums.append(0.0)
                #self.dtExitSamples.append(0)
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

            '''
            # processing the new time between exits. No batch means needed here, just the average
            exitS = [ll.exitTimeS for ll in log]
            exitS.sort()
            if len(exitS) > 1:
                self.dtExitSums[epIdx] += exitS[-1]-exitS[0]
                self.dtExitSamples[epIdx] += len(exitS)-1'''


            #batch means also for throughput
            exitS = [ll.exitTimeS for ll in log]
            exitS.sort()
            # We compute the throughput over small windows (size self.thrWindowS), as the number of completed requests in the timeframe
            nWindows = (exitS[-1]-exitS[0])//self.thrWindowS
            completionsInWindow = [0]*int(nWindows+1)
            for e in exitS:
                completionsInWindow[int((e-exitS[0])//self.thrWindowS)] += 1
            # last window is incomplete: it will be discarded
            del completionsInWindow[-1]
            thrS = [ciw*1.0/self.thrWindowS for ciw in completionsInWindow]
            # adding the throughputs into the batches, ensuring that each batch is long at most K
            startFrom = 0

            if self.thrSamples[epIdx]%self.K > 0: # if some batch is not full
                toAdd = self.K-(self.thrSamples[epIdx]%self.K)
                self.thrBatches[epIdx][-1] += thrS[startFrom:startFrom+toAdd]
                startFrom = startFrom+toAdd

            # add new batches as needed (last one might not be full)
            for i in range(startFrom, len(thrS), self.K):
                self.thrBatches[epIdx].append(thrS[i:i+self.K])

            # count the new samples
            self.thrSamples[epIdx] += len(thrS)

    def computeStats(self):
        stats = MsStats()
        for label in self.epIdxs:
            epIdx = self.epIdxs[label]
            if self.rtSamples[epIdx] < 3*self.K:
                rtMeans = np.array([float('NaN'), float('NaN')])
                CI = (float('NaN'), float('NaN'))
            else:
                rtarr = np.array(self.rtBatches[epIdx][0:self.rtSamples[epIdx]//self.K])
                rtMeans = np.mean(rtarr, axis=1)
                CI = st.t.interval(0.99, len(rtMeans[1:]) - 1, loc=np.mean(rtMeans[1:]), scale=st.sem(rtMeans[1:]))
            stats.rtCI[label] = CI
            stats.rtMean[label] = np.mean(rtMeans[1:])
            stats.rtBatchesNum[label] = self.rtSamples[epIdx]//self.K
            stats.nrSamples[label] = self.rtSamples[epIdx]
            '''if self.dtExitSums[epIdx] > 0:
                #print(label, self.dtExitSamples[epIdx], self.dtExitSums[epIdx])
                stats.thrMean[label] = self.dtExitSamples[epIdx]/self.dtExitSums[epIdx]
            else:
                stats.thrMean[label] = None'''
            if self.thrSamples[epIdx] < 3*self.K:
                thrMeans = np.array([float('NaN'), float('NaN')])
                CI = (float('NaN'), float('NaN'))
            else:
                thrarr = np.array(self.thrBatches[epIdx][0:self.thrSamples[epIdx]//self.K])
                thrMeans = np.mean(thrarr, axis=1)
                CI = st.t.interval(0.99, len(thrMeans[1:]) - 1, loc=np.mean(thrMeans[1:]), scale=st.sem(thrMeans[1:]))
            stats.thrCI[label] = CI
            stats.thrMean[label] = np.mean(thrMeans[1:])
            stats.thrBatchesNum[label] = self.thrSamples[epIdx]//self.K
        return stats