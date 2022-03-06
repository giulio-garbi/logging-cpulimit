package org.sysma.loggingcpulimit.loadgen.teastore;

public class Stopper implements Runnable {
	private final Thread tL;
	private final Thread[] tW;
	
	public Stopper(Thread tL, Thread[] tW) {
		this.tL = tL;
		this.tW = tW;
	}
	
	@Override
	public void run() {
		for(Thread t:tW) 
			t.interrupt();
		for(Thread t:tW)
			try {
				t.join();
			} catch (InterruptedException e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
			}
		try {
			tL.join();
		} catch (InterruptedException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
	}

}
