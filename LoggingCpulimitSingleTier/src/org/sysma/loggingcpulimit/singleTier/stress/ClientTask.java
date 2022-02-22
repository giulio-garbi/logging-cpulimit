package org.sysma.loggingcpulimit.singleTier.stress;

import java.io.IOException;
import java.util.concurrent.ExecutionException;

import org.sysma.schedulerExecutor.Communication;
import org.sysma.schedulerExecutor.estimation.EstimationTask;

public class ClientTask extends EstimationTask<Void> {
	
	@Override
	public void main(Communication comm, Void arg) throws InterruptedException {
		Thread.sleep(50);
		try {
			comm.asyncCallRegistry("srv1", "service", (x)->{}).get().close();
		} catch (IOException | ExecutionException e) {
			e.printStackTrace();
		}
	}

}
