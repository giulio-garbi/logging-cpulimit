package org.sysma.loggingcpulimit.singleTier;

import java.io.IOException;

import org.sysma.schedulerExecutor.Communication;
import org.sysma.schedulerExecutor.EntryDef;
import org.sysma.schedulerExecutor.TaskDef;
import org.sysma.schedulerExecutor.TaskDefinition;

@TaskDef(name="srv1")
public class SingleTierServer extends TaskDefinition {
	@EntryDef("service")
	public void service(Communication comm) throws IOException {
		comm.respond(200, "hello world".getBytes());
	}
}
