package org.sysma.schedulerExecutor.estimation;

import java.io.IOException;
import java.time.Duration;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.function.Function;

import org.sysma.schedulerExecutor.LogLine;
import org.sysma.schedulerExecutor.TaskDump;
import org.sysma.schedulerExecutor.LogLine.Begin;
import org.sysma.schedulerExecutor.LogLine.End;
import org.sysma.schedulerExecutor.MainTaskDefinition;

public abstract class EstimationTask<T> extends MainTaskDefinition<T> {
	HashMap<String, Double> rtMean = null;
	HashMap<String, Double> thrMean = null;
	int nClients;

	public void estimateEntriesRTAndThroughput(Duration length, Duration waitBeforeCollect, int nClients, Function<Integer, T> fArgs) throws IOException {
		HashMap<String, BatchMeans> rtBatches = new HashMap<>();
		//HashMap<String, BatchMeans> thrBatches = new HashMap<>();
		HashMap<String, BatchMeans> tbcBatches = new HashMap<>();
		boolean converged;
		this.nClients = nClients;
		
		do {
			ArrayList<String> logParts = startRegistry(length, waitBeforeCollect, nClients, fArgs);
			StringBuilder log = new StringBuilder("[");
			for(int i=0; i<logParts.size(); i++) {
				log.append(logParts.get(i));
				if(i<logParts.size()-1)
					log.append(", ");
				else
					log.append("]");
			}
			TaskDump[] tds = TaskDump.fromJsons(log.toString());
			
			HashMap<String, HashMap<String, Long>> beginTime = new HashMap<>();
			HashMap<String, HashMap<String, Long>> endTime = new HashMap<>();
			
			for(TaskDump td:tds) {
				if(!td.taskName.equals("registry")) {
					for(LogLine lline:td.log) {
						switch(lline.kind) {
						case "begin":
							Begin begin = (Begin) lline;
							beginTime.computeIfAbsent(begin.taskName+"-"+begin.entryName, 
									(x)->new HashMap<>()).put(begin.client, begin.time);
							break;
						case "end":
							End end = (End) lline;
							endTime.computeIfAbsent(end.taskName+"-"+end.entryName, 
									(x)->new HashMap<>()).put(end.client, end.time);
							break;
						}
					}
				}
			}
			
			for(String taskEntry:beginTime.keySet()) {
				var btimes = beginTime.get(taskEntry);
				var etimes = endTime.get(taskEntry);
				for(String client:btimes.keySet()) {
					if(etimes.containsKey(client)) {
						long ms = etimes.get(client) - btimes.get(client);
						rtBatches.computeIfAbsent(taskEntry, x->new BatchMeans(30,30)).addSample(ms/1000.0);
					}
				}
				Long[] sortedExitTimes = etimes.values().stream().sorted().toArray(Long[]::new);
				
				/*
				final long dtMs = 100;
				ArrayList<Long> spacedTimeIntervals = new ArrayList<>();
				for(Long t = sortedExitTimes[0]; t<sortedExitTimes[sortedExitTimes.length-1]; t+= dtMs) {
					spacedTimeIntervals.add(t);
				}
				spacedTimeIntervals.add(sortedExitTimes[sortedExitTimes.length-1]);
				int setPtr = 0;
				for(int i=1; i<spacedTimeIntervals.size(); i++) {
					int howManyServed = 0;
					while(setPtr<sortedExitTimes.length && sortedExitTimes[setPtr]<spacedTimeIntervals.get(i)) {
						howManyServed++;
						setPtr++;
					}
					double dt = (spacedTimeIntervals.get(i)-spacedTimeIntervals.get(i-1))/1000.0;
					thrBatches.computeIfAbsent(taskEntry, x->new BatchMeans(50,50)).addSample(1.0*howManyServed/dt);
				}*/
				for(int i=1; i<sortedExitTimes.length; i++) {
					double tbc = (sortedExitTimes[i]-sortedExitTimes[i-1])/1000.0;
					tbcBatches.computeIfAbsent(taskEntry, x->new BatchMeans(30,30)).addSample(tbc);
				}
			}
			
			converged = true;
			for(var bm:rtBatches.entrySet()) {
				double ciError = bm.getValue().ciError();
				converged &= ciError <= 0.1;
				System.out.println("rt "+bm.getKey()+" : "+bm.getValue().mean()+" "+ciError+" "+bm.getValue().Bm2.getN());
			}
			/*for(var bm:thrBatches.entrySet()) {
				double ciError = bm.getValue().ciError();
				converged &= ciError <= 0.1;
				System.out.println("thr "+bm.getKey()+" : "+bm.getValue().mean()+" "+ciError+" "+bm.getValue().Bm2.getN());
			}*/
			for(var bm:tbcBatches.entrySet()) {
				double ciTbcError = bm.getValue().ciError();
				double meanTbc = bm.getValue().mean();
				double upperTbc = meanTbc+ciTbcError;
				
				double lowerThr = 1.0/upperTbc;
				double meanThr = 1.0/meanTbc;
				
				double thrError = meanThr-lowerThr;
				//converged &= meanTbc > 0 && thrError <= 0.1;
				System.out.println("thr "+bm.getKey()+" : "+meanThr+" "+thrError+" "+bm.getValue().Bm2.getN());
			}
		} while(!converged);
		
		rtMean = new HashMap<>();
		rtBatches.forEach((te, batch)->{rtMean.put(te, batch.mean());});

		/*thrMean = new HashMap<>();
		thrBatches.forEach((te, batch)->{thrMean.put(te, batch.mean());});*/
		thrMean = new HashMap<>();
		tbcBatches.forEach((te, batch)->{thrMean.put(te, 1.0/batch.mean());});
	}
	
	public String makeCSV() {
		StringBuilder csv = new StringBuilder();
		csv.append("cli; entry; Client-main; "+nClients+"\n");
		rtMean.forEach((te, rt)->{
			csv.append("response time; entry; "+te+"; "+rt+"\n");
		});
		thrMean.forEach((te, thr)->{
			csv.append("throughput; entry; "+te+"; "+thr+"\n");
		});
		return csv.toString();
	}
}
