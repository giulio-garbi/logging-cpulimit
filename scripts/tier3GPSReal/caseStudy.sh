bash initServer.sh &
sleep 1
bash changeConcurServer.sh $2
java -Djava.compiler=NONE -jar ../../data/tier3GPSReal/three_tier.jar cli $1 140 60000 http://127.0.0.1:9000 ../../data/tier3GPSReal/case-$1-$2.csv
pkill java