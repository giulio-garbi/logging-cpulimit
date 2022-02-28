if [ -f /sys/fs/cgroup/cpu/3tier/ ]
then
	sudo cgdelete -g cpu:3tier
fi
sudo cgcreate -g cpu:3tier
