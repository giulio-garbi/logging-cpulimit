package org.sysma.loggingcpulimit.singleTier;

import java.io.IOException;
import java.util.concurrent.atomic.AtomicInteger;

import org.sysma.schedulerExecutor.Communication;
import org.sysma.schedulerExecutor.EntryDef;
import org.sysma.schedulerExecutor.TaskDef;
import org.sysma.schedulerExecutor.TaskDefinition;

@TaskDef(name="srv1")
public class SingleTierServer extends TaskDefinition {
	public static double nCores = 1.0;
	private static final AtomicInteger clientsUsing = new AtomicInteger(0);
	@EntryDef("/service")
	public void service(Communication comm) throws IOException, InterruptedException {
		double sTime = 50 * Math.max(1.0, clientsUsing.incrementAndGet()/nCores);
		Thread.sleep((int)sTime);
		clientsUsing.decrementAndGet();
		comm.respond(200, "hello world".getBytes());
	}
}
