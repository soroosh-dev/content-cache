# content-cache
A content cache system implemented with Django.

# Setup
Run setup.sh with root priviledges and pass username as it's first argument.

```
sudo ./setup.sh username
```

# Configurations
Update ccache/ccache/settings.py file and add server's IP address or domain name to ALLOWED_HOSTS; Remember to include localhost in the list as well.

Update conf/nginx.conf file and set appropriate paths for ```lua_package_path``` in line 13. You should also update the path in which uploads.log file saves in line 61.

## Considerations for uploads.log file
This file contains log records about uploaded files in content-cache system. By default setup.sh creates a uploads.log file inside logs directory. All you need to do is to update line 61 with absolute path to this file.
If you chose to use another path for this file use these commands to generate log file and then update nginx.conf file with new path for log file.

```
touch /path/to/new/logfile.log
chown nobody:nogroup /path/to/new/log/file.log
```
Then update nginx.conf file.

# Starting the server
In order to start the server run ./start.sh file.

# Stopping the server
In order to stop the server, use command ```ps aux | grep nginx``` to find out master process's PID, then use kill command to stop the server.

# Notes
- API endpoints are provided using postman collection.
- ./logs/uploads.log file contains log records about uploaded files.



