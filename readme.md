### colconf

This is a script for collecting cisco startup config files to scp server.

- First of all, install requirements:
```commandline
pip install -r requirements.txt
```

- Make file <font color='red'><b>devices.txt</b></font> in the folder containing this script.
Fill the file with ip addresses of your devices, <b>each on new line</b>.

- make file <font color='red'><b>conf.py</b></font> and fill with following data:

```
#ip of your scp server:
SERVER_IP = 'xxx.xxx.xxx.xxx'

#relative path to forder for devices' configs:
FOLDER_PATH = 'folder/next_folder/'
#If you want to place files to scp server user's root directory, use empty string ''.
```