package org.sysma.loggingcpulimit.tier3GPS.stress;

import java.io.BufferedWriter;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStreamWriter;
import java.io.Writer;
import java.math.BigDecimal;
import java.time.Duration;

import org.sysma.loggingcpulimit.tier3GPS.ExecParams;
import org.sysma.loggingcpulimit.tier3GPS.TierOne;
import org.sysma.loggingcpulimit.tier3GPS.TierThree;
import org.sysma.loggingcpulimit.tier3GPS.TierTwo;
import org.sysma.schedulerExecutor.TaskDefinition;
import org.sysma.schedulerExecutor.TaskDirectory;

public class Main {
	public static void main(String[] args) throws IOException {
		int nCli = args.length>0?Integer.parseInt(args[0]):10;
		BigDecimal nSrv = args.length>0?new BigDecimal(args[1]):BigDecimal.valueOf(3);
		
		long think = args.length>0?Integer.parseInt(args[2]):200;
		long srv1 = args.length>0?Integer.parseInt(args[3]):200;
		long srv2 = args.length>0?Integer.parseInt(args[4]):200;
		long srv3 = args.length>0?Integer.parseInt(args[5]):200;
		
		int regport = args.length>0?Integer.parseInt(args[6]):9099;
		int srv1port = args.length>0?Integer.parseInt(args[7]):9081;
		int srv2port = args.length>0?Integer.parseInt(args[8]):9082;
		int srv3port = args.length>0?Integer.parseInt(args[9]):9083;
		String outFn = args.length>0?args[10]:null;
		
		ExecParams.allTiersCores = nSrv.doubleValue();
		ClientTask.thinkTime = think;
		
		var registry = TaskDirectory.instantiateRegistry(regport, 9999);
		registry.start();
		
		System.out.println("I&R Service 1");
		TierOne.stdServiceTime = srv1;
		var s1tk = TaskDefinition.instantiate(TierOne.class, srv1port, 9999);
		s1tk.start();
		TaskDirectory.register(TierOne.class, srv1port);
		
		System.out.println("I&R Service 2");
		TierTwo.stdServiceTime = srv2;
		var s2tk = TaskDefinition.instantiate(TierTwo.class, srv2port, 9999);
		s2tk.start();
		TaskDirectory.register(TierTwo.class, srv2port);
		
		System.out.println("I&R Service 3");
		TierThree.stdServiceTime = srv3;
		var s3tk = TaskDefinition.instantiate(TierThree.class, srv3port, 9999);
		s3tk.start();
		TaskDirectory.register(TierThree.class, srv3port);
		
		ClientTask cli = new ClientTask();
		cli.estimateEntriesRTAndThroughput(Duration.ofSeconds(60), Duration.ofSeconds(1), nCli, x->null);
		if(outFn == null) {
			System.out.println(cli.makeCSV());
		} else {
			try (Writer writer = new BufferedWriter(new OutputStreamWriter(
			              new FileOutputStream(outFn)))) {
			   writer.write(cli.makeCSV());
			}
		}
		s1tk.stop();
		s2tk.stop();
		s3tk.stop();
		registry.stop();
	}
}
