java -Djava.compiler=NONE -jar ../../data/tier3GPSReal/three_tier.jar reg 9000
sudo cgexec -g cpu:3tier --sticky java -Djava.compiler=NONE -jar ../../data/tier3GPSReal/three_tier.jar srv 22 50 36 http://127.0.0.1:9000 9001 9002 9003