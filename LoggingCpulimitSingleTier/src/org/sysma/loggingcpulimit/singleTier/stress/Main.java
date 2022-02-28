package org.sysma.loggingcpulimit.singleTier.stress;

import java.io.BufferedWriter;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStreamWriter;
import java.io.Writer;
import java.time.Duration;

import org.sysma.loggingcpulimit.singleTier.SingleTierServer;
import org.sysma.schedulerExecutor.TaskDefinition;
import org.sysma.schedulerExecutor.TaskDirectory;

public class Main {
	public static void main(String[] args) throws IOException {
		int nCli = args.length>0?Integer.parseInt(args[0]):10;
		int nSrv = args.length>0?Integer.parseInt(args[1]):7;
		int regport = args.length>0?Integer.parseInt(args[2]):9099;
		int srvport = args.length>0?Integer.parseInt(args[3]):9081;
		String outFn = args.length>0?args[4]:null;
		
		SingleTierServer.nCores = nSrv;
		
		var registry = TaskDirectory.instantiateRegistry(regport, 9999);
		registry.start();
		System.out.println("I&R Service ");
		var atk = TaskDefinition.instantiate(SingleTierServer.class, srvport, 9999);
		atk.start();
		TaskDirectory.register(SingleTierServer.class, srvport);
		
		ClientTask cli = new ClientTask();
		cli.estimateEntriesRTAndThroughput(Duration.ofSeconds(50), Duration.ofSeconds(1), nCli, x->null);
		if(outFn == null) {
			System.out.println(cli.makeCSV());
		} else {
			try (Writer writer = new BufferedWriter(new OutputStreamWriter(
			              new FileOutputStream(outFn)))) {
			   writer.write(cli.makeCSV());
			}
		}
		atk.stop();
		registry.stop();
	}
}
