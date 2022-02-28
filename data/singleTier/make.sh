cat cases.txt | while read y
do
	java -jar single_tier.jar $y 
done