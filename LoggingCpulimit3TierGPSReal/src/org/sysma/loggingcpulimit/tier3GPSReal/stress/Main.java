package org.sysma.loggingcpulimit.tier3GPSReal.stress;

import java.io.BufferedWriter;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStreamWriter;
import java.io.Writer;
import java.net.URI;
import java.time.Duration;

import org.sysma.loggingcpulimit.tier3GPSReal.TierOne;
import org.sysma.loggingcpulimit.tier3GPSReal.TierThree;
import org.sysma.loggingcpulimit.tier3GPSReal.TierTwo;
import org.sysma.schedulerExecutor.TaskDefinition;
import org.sysma.schedulerExecutor.TaskDirectory;

public class Main {
	public static void main(String[] args) throws IOException {
		if(args.length == 0) {
			usage();
			return;
		}
		switch(args[0]) {
			case "cli":
				if(args.length == 6) {
					mainCli(args);
				} else {
					usage();
					return;
				}
			break;
			case "srv":
				if(args.length == 8) {
					mainSrv(args);
				} else {
					usage();
					return;
				}
			break;
			case "reg":
				if(args.length == 2) {
					mainReg(args);
				} else {
					usage();
					return;
				}
			break;
			default:
				usage();
				return;
		}
	}
	
	public static void usage() {
		System.out.println("Usage:");
		System.out.println("cli <n_cli> <think_ms> <batch_ms> <reg_URI> <out_file>");
		System.out.println("srv <srv1_itr> <srv2_itr> <srv3_itr> <reg_URI> <srv1_port> <srv2_port> <srv3_port>");
		System.out.println("reg <reg_port>");
	}
	
	public static void mainCli(String[] args) throws IOException {
		int nCli = Integer.parseInt(args[1]);
		long think = Long.parseLong(args[2]);
		long batchLength = Long.parseLong(args[3]);
		URI regURI = URI.create(args[4]);
		String outFn = args[5];
		
		ClientTask.thinkTime = think;
		
		TaskDirectory.setRegistry(regURI);
		
		ClientTask cli = new ClientTask();
		cli.estimateEntriesRTAndThroughput(Duration.ofMillis(batchLength), Duration.ofSeconds(1), nCli, x->null);
		if(outFn == null) {
			System.out.println(cli.makeCSV());
		} else {
			try (Writer writer = new BufferedWriter(new OutputStreamWriter(
			              new FileOutputStream(outFn)))) {
			   writer.write(cli.makeCSV());
			}
		}
	}
	
	public static void mainSrv(String[] args) throws IOException {
		long srv1 = Long.parseLong(args[1]);
		long srv2 = Long.parseLong(args[2]);
		long srv3 = Long.parseLong(args[3]);
		
		URI regURI = URI.create(args[4]);
		int srv1port = Integer.parseInt(args[5]);
		int srv2port = Integer.parseInt(args[6]);
		int srv3port = Integer.parseInt(args[7]);
		
		TaskDirectory.setRegistry(regURI);
		
		System.out.println("I&R Service 1");
		TierOne.n_iter = srv1;
		var s1tk = TaskDefinition.instantiate(TierOne.class, srv1port, 9999);
		s1tk.start();
		TaskDirectory.register(TierOne.class, srv1port);
		
		System.out.println("I&R Service 2");
		TierTwo.n_iter = srv2;
		var s2tk = TaskDefinition.instantiate(TierTwo.class, srv2port, 9999);
		s2tk.start();
		TaskDirectory.register(TierTwo.class, srv2port);
		
		System.out.println("I&R Service 3");
		TierThree.n_iter = srv3;
		var s3tk = TaskDefinition.instantiate(TierThree.class, srv3port, 9999);
		s3tk.start();
		TaskDirectory.register(TierThree.class, srv3port);
	}
	
	public static void mainReg(String[] args) throws IOException {
		int regport = Integer.parseInt(args[1]);
		
		System.out.println("I&R Registry");
		var registry = TaskDirectory.instantiateRegistry(regport, 9999);
		registry.start();
	}
}
