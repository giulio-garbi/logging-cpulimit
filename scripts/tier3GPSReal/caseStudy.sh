java -Djava.compiler=NONE -jar ../../data/tier3GPSReal/three_tier.jar reg 9000 &
REG=$!
sleep 1
sudo cgexec -g cpu:3tier --sticky java -Djava.compiler=NONE -jar ../../data/tier3GPSReal/three_tier.jar srv 220 500 360 http://127.0.0.1:9000 9001 9002 9003 &
SRV=$!
sleep 10
bash changeConcurServer.sh $2
java -Djava.compiler=NONE -jar ../../data/tier3GPSReal/three_tier.jar cli $1 140 60000 http://127.0.0.1:9000 ../../data/tier3GPSReal/case-$1-$2.csv
kill $REG
kill $SRV