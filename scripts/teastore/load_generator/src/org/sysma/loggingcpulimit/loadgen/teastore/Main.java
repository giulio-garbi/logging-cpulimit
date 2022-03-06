package org.sysma.loggingcpulimit.loadgen.teastore;

public class Main {
	
	public static void usage() {
		System.out.println("Usage: <nCli> <thinkS> <ip:port> <out.txt>");
	}

	public static void main(String[] args) {
		if(args.length != 5) {
			usage(); 
			return;
		}
		String outFname = args[4];
		int nCli = Integer.parseInt(args[1]);
		String reqAddr = "http://"+args[3]+"/tools.descartes.teastore.webui/";
		double thinkS = Double.parseDouble(args[2]);
		
		Logger logger = new Logger(outFname, nCli);
		Workload[] wloads = new Workload[nCli];
		for(int i=0; i<nCli; i++)
			wloads[i] = new Workload(logger.output, thinkS, reqAddr);
		wloads[0].print = true;
		
		Thread tL = new Thread(logger);
		tL.start();
		Thread[] tW = new Thread[nCli];
		for(int i=0; i<nCli; i++) {
			tW[i] = new Thread(wloads[i]);
			tW[i].start();
		}
		
		Thread tS = new Thread(new Stopper(tL, tW));
		Runtime.getRuntime().addShutdownHook(tS);
	}

}
