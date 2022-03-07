package org.sysma.loggingcpulimit.loadgen.teastore;

import java.time.Duration;
import java.time.Instant;
import java.time.temporal.Temporal;
import java.util.List;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.TimeUnit;

import org.apache.hc.client5.http.classic.methods.HttpGet;
import org.apache.hc.client5.http.classic.methods.HttpPost;
import org.apache.hc.client5.http.config.RequestConfig;
import org.apache.hc.client5.http.impl.classic.CloseableHttpClient;
import org.apache.hc.client5.http.impl.classic.HttpClients;
import org.apache.hc.core5.http.ConnectionReuseStrategy;
import org.apache.hc.core5.http.HttpRequest;
import org.apache.hc.core5.http.HttpResponse;

import java.io.IOException;
import java.math.BigDecimal;
import java.net.URI;
//import java.net.http.HttpClient;
//import java.net.http.HttpRequest;
//import java.net.http.HttpResponse.BodyHandlers;

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
	
	private static final ConnectionReuseStrategy NO_REUSE = new ConnectionReuseStrategy() {
		@Override
		public boolean keepAlive(HttpRequest request, HttpResponse response,
				org.apache.hc.core5.http.protocol.HttpContext context) {
			return false;
		}};

	@Override
	public void run() {
		Duration sumReq = Duration.ZERO;
		int nCycles = 0;
		try {
			try(CloseableHttpClient client = HttpClients.custom()
					.setConnectionReuseStrategy(NO_REUSE)
					.setDefaultRequestConfig(RequestConfig.custom()
					.setResponseTimeout(1, TimeUnit.DAYS)
					.setConnectionRequestTimeout(1, TimeUnit.DAYS)
					.setConnectTimeout(1, TimeUnit.DAYS).build())
					.build();){
				Instant firstStart = Instant.now();
				while(!Thread.interrupted()) {
					Instant start = Instant.now();
					Thread.sleep((int)(thinkS*1000));
					HttpGet request = new HttpGet(URI.create(reqAddr));
					
					try {
						Instant startReq = Instant.now();
						var ans = client.execute(request);
						ans.close();
						Instant stopReq = Instant.now();
						sumReq = sumReq.plus(Duration.between(startReq, stopReq));
					} catch (IOException e) {
						e.printStackTrace();
					} 
					Instant end = Instant.now();
					nCycles++;
					//record(start, end);
					if(print && nCycles%100==0) {
						System.out.println("cycle "+Duration.between(firstStart, Instant.now()).dividedBy(nCycles).toMillis() + " req " + sumReq.dividedBy(nCycles).toMillis());
						firstStart = Instant.now();
						sumReq = Duration.ZERO;
						nCycles = 0;
					}
				}
			} catch (IOException e1) {
				// TODO Auto-generated catch block
				e1.printStackTrace();
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
