java -Djava.compiler=NONE -jar ../../data/tier3GPSReal/three_tier.jar reg 9000 &
REG=$!
sleep 1
java -Djava.compiler=NONE -jar ../../data/tier3GPSReal/three_tier.jar srv 220 500 360 http://127.0.0.1:9000 9001 9002 9003 &
SRV=$!
sleep 10
java -Djava.compiler=NONE -jar ../../data/tier3GPSReal/three_tier.jar cli $1 140 300000 http://127.0.0.1:9000 ../../data/tier3GPSReal/nocpul-case-$1-$2.csv
sudo pkill java
sleep 10