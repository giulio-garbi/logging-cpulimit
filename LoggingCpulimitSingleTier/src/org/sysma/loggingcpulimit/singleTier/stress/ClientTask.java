package org.sysma.loggingcpulimit.singleTier.stress;

import java.io.IOException;
import java.util.concurrent.ExecutionException;

import org.apache.commons.math3.distribution.ExponentialDistribution;
import org.sysma.schedulerExecutor.Communication;
import org.sysma.schedulerExecutor.estimation.EstimationTask;

public class ClientTask extends EstimationTask<Void> {
	
	@Override
	public void main(Communication comm, Void arg) throws InterruptedException {
		ExponentialDistribution dist = new ExponentialDistribution(250);
		Thread.sleep((int)dist.sample());
		try {
			comm.asyncCallRegistry("srv1", "service", (x)->{}).get().close();
		} catch (IOException | ExecutionException e) {
			e.printStackTrace();
		}
	}

}
