cat whatif_same_concur/allcases.txt | while read y
do
	java -jar three_tier.jar $y
done