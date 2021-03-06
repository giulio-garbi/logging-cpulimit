package org.sysma.loggingcpulimit.tier3GPSReal;

import java.io.IOException;
import java.util.concurrent.ExecutionException;

import org.sysma.schedulerExecutor.Communication;
import org.sysma.schedulerExecutor.EntryDef;
import org.sysma.schedulerExecutor.TaskDef;
import org.sysma.schedulerExecutor.TaskDefinition;

@TaskDef(name="srv1")
public class TierOne extends TaskDefinition {
	public static long n_iter;
	
	@EntryDef("/service")
	public void service(Communication comm) throws IOException, InterruptedException, ExecutionException {
		comm.asyncCallRegistry("srv2", "service", x->{}).get().close();
		
		//task: compute `mtxOut = mtxIn * mtxIn` n_iter times
		int[][] mtxIn = new int [20][20];
		int[][] mtxOut = new int [20][20];
		for(long i=0; i<n_iter; i++) {
			for(int a=0; a<mtxOut.length; a++) {
				for(int b=0; b<mtxOut[a].length; b++) {
					mtxOut[a][b] = 0;
					for(int c = 0; c<mtxIn.length; c++)
						mtxOut[a][b] += mtxIn[a][c] * mtxIn[c][b];
				}
			}
		}
		
		comm.respond(200, "hello world".getBytes());
	}
}
