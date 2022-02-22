package org.sysma.schedulerExecutor.estimation;

import org.apache.commons.math3.distribution.TDistribution;
import org.apache.commons.math3.stat.descriptive.SummaryStatistics;
import org.apache.commons.math3.util.Pair;

import java.util.ArrayList;
import java.util.List;

public class BatchMeans {
	protected int N, K;
	protected List<List<Double>> B;
	protected SummaryStatistics Bm2;
	
	protected final float confLvl = 0.99f;
	
	public BatchMeans(int N, int K) {
		this.N = N; //minimum number of batches
		this.K = K; //batch size
		this.B = new ArrayList<>(); //batch data
		this.Bm2 = new SummaryStatistics(); //each batch mean, skip first
	}
	
	public void addSample(double v) {
		if(B.size() == 0) {
			B.add(new ArrayList<>());
		} else if (B.get(B.size()-1).size() == K) {
			float sum = 0;
			for(var i:B.get(B.size()-1)) {
				sum += i;
			}
			if(B.size()>1) //skip first batch
				Bm2.addValue(sum/K);
			B.add(new ArrayList<>());
		}
		B.get(B.size()-1).add(v);
	}
	
	public Pair<Double, Double> computeCI() {
		//Computes the conficence interval over each batch means (excluding the first)
		//https://gist.github.com/gcardone/5536578
		
		if(Bm2.getN() + 1 < N)
			return null;
		
		long df = Bm2.getN()-1;
		if(df < 1)
			return null;
		
		TDistribution tDist = new TDistribution(df);
		double critVal = tDist.inverseCumulativeProbability(1.0 - (1 - confLvl) / 2);
		double ciWidth = critVal * Bm2.getStandardDeviation() / Math.sqrt(Bm2.getN());
		double lowCi = Bm2.getMean() - ciWidth;
		double upCi = Bm2.getMean() + ciWidth;
		return Pair.create(lowCi, upCi);
	}
	
	public double ciError() {
		var ci = computeCI();
		if(ci == null)
			return Double.POSITIVE_INFINITY;
		return Math.abs(ci.getSecond()-ci.getFirst())/2;
	}
	
	public double mean() {
		return Bm2.getMean();
	}
}
