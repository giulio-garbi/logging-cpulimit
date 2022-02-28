package org.sysma.loggingcpulimit.tier3GPS;

import java.io.IOException;
import java.util.concurrent.ExecutionException;

import org.sysma.schedulerExecutor.Communication;
import org.sysma.schedulerExecutor.EntryDef;
import org.sysma.schedulerExecutor.TaskDef;
import org.sysma.schedulerExecutor.TaskDefinition;

@TaskDef(name="srv1")
public class TierOne extends TaskDefinition {
	public static long stdServiceTime;
	
	@EntryDef("/service")
	public void service(Communication comm) throws IOException, InterruptedException, ExecutionException {
		comm.asyncCallRegistry("srv2", "service", x->{}).get().close();
		double sTime = stdServiceTime * Math.max(1.0, ExecParams.allTiersClientsUsing.incrementAndGet()/ExecParams.allTiersCores);
		Thread.sleep((int)sTime);
		ExecParams.allTiersClientsUsing.decrementAndGet();
		comm.respond(200, "hello world".getBytes());
	}
}
