package org.sysma.loggingcpulimit.loadgen.teastore;

import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;
import java.util.concurrent.LinkedBlockingQueue;

public class Logger implements Runnable {
	
	public final LinkedBlockingQueue<String> output = new LinkedBlockingQueue<>();
	public final String filename;
	public final int nWorkers;
	public Logger(String filename, int nWorkers) {
		this.filename = filename;
		this.nWorkers = nWorkers;
	}

	@Override
	public void run() {
		try {
			int stoppedWorkers = 0;
			try(FileWriter fw = new FileWriter(filename, false);
			BufferedWriter bw = new BufferedWriter(fw);){
				while(stoppedWorkers < nWorkers) {
					String line = output.take();
					if(line.equals("stop"))
						stoppedWorkers++;
					bw.write(line);
					bw.newLine();
					bw.flush();
				}
			}
		} catch (IOException | InterruptedException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}

}
