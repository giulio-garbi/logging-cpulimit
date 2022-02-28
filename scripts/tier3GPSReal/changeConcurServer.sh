sudo cgset -r cpu.cfs_period_us=100000 3tier  
sudo cgset -r cpu.cfs_quota_us=`python3 -c "print('%d'%(${1}*100000))"` 3tier