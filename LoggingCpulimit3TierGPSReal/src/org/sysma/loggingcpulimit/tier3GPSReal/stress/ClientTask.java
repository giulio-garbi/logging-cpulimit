package org.sysma.loggingcpulimit.tier3GPSReal.stress;

import java.io.IOException;
import java.util.concurrent.ExecutionException;

import org.apache.commons.math3.distribution.ExponentialDistribution;
import org.sysma.schedulerExecutor.Communication;
import org.sysma.schedulerExecutor.estimation.EstimationTask;

public class ClientTask extends EstimationTask<Void> {
	
	public static long thinkTime;
	
	@Override
	public void main(Communication comm, Void arg) throws InterruptedException {
		ExponentialDistribution dist = new ExponentialDistribution(thinkTime);
		Thread.sleep((int)dist.sample());
		try {
			comm.asyncCallRegistry("srv1", "service", (x)->{}).get().close();
		} catch (IOException | ExecutionException e) {
			e.printStackTrace();
		}
	}

}
