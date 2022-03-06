package org.sysma.loggingcpulimit.loadgen.teastore;

import java.time.Duration;
import java.time.Instant;
import java.time.temporal.Temporal;
import java.util.concurrent.LinkedBlockingQueue;
import java.io.IOException;
import java.math.BigDecimal;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse.BodyHandlers;

public class Workload implements Runnable{
	private final double thinkS;
	private final LinkedBlockingQueue<String> output;
	private final String reqAddr;
	public boolean print = false;
	
	public Workload(LinkedBlockingQueue<String> output, double thinkS, String reqAddr) {
		this.thinkS = thinkS;
		this.output = output;
		this.reqAddr = reqAddr;
	}

	@Override
	public void run() {
		Duration sumCycles = Duration.ZERO;
		Duration sumReq = Duration.ZERO;
		int nCycles = 0;
		try {
			HttpClient client = HttpClient.newHttpClient();
			while(!Thread.interrupted()) {
				Instant start = Instant.now();
				Thread.sleep((int)(thinkS*1000));
				HttpRequest request = HttpRequest.newBuilder()
				         .uri(URI.create(reqAddr))
				         .build();
				try {
					Instant startReq = Instant.now();
					client.send(request, BodyHandlers.ofString());
					Instant stopReq = Instant.now();
					sumReq = sumReq.plus(Duration.between(startReq, stopReq));
				} catch (IOException e) {
					e.printStackTrace();
				} 
				Instant end = Instant.now();
				nCycles++;
				sumCycles = sumCycles.plus(Duration.between(start, end));
				//record(start, end);
				if(print && nCycles%100==0)
					System.out.println("cycle "+sumCycles.dividedBy(nCycles).toMillis() + " req " + sumReq.dividedBy(nCycles).toMillis());
			}
		} catch (InterruptedException e) {}
		stop();
	}
	
	private void record(Instant start, Instant end) {
		BigDecimal startS = BigDecimal.valueOf(start.getEpochSecond())
				.add(BigDecimal.valueOf(start.getNano(), 9));
		BigDecimal endS = BigDecimal.valueOf(end.getEpochSecond())
				.add(BigDecimal.valueOf(end.getNano(), 9));
		BigDecimal rtS = endS.subtract(startS);
		BigDecimal rtUsec = rtS.movePointRight(6);
		
		String end_ms = endS.movePointRight(3).toPlainString();
		String rt_usec = rtUsec.toPlainString();
		String code = "200";
		String req = "main";
		String line = "end_ms:"+end_ms+" rt_usec:"+rt_usec+" code:"+code+" req:\""+req+"\"";
		output.add(line);
	}
	
	private void stop() {
		output.add("stop");
	}

}
