This code base was used for extending dolphin with twitter support. It assumes the user to have a twitter account.
Additionaly, user needs to set up a twitter application on https://developer.twitter.com/apps 

In the "Client" directory:  
1. data_file.txt : It holds the data to be sent
2. refresh.py : It has various utility functions to conduct the experiment. The smartphone's bluetooth address needs to be manually set in this file in global field "BT_ADDR".
3. optimized_encrypt_client.py : It conducts the actual tweeting experiments as client sending tweets to server. The server's phone number needs to be manually set in this file in global field "SERV_NO". Also, it requires pulseaudio sink name on client's linux machine which needs to be manually set in this file in global field "SINK_NAME".

A user needs to run optimized_encrypt_client.py with following paramters: 
```
python3 optimized_encrypt_client.py <data_file> <size_in_bytes> <data_rate_in_bps> <number_of_tests>
```

In the "Server" directory:
1. refresh.py : It has various utility functions to conduct the experiment. The smartphone's bluetooth address needs to be manually set in this file in global field "BT_ADDR".
2. optimized_encrypt_server.py : It receives tweets from client and posts on behalf of client. Also, it requires pulseaudio sink name on server's linux machine which needs to be manually set in this file in global field "SINK_NAME".

A user needs to run optimized_encrypt_server.py with following paramters: 
```
python3 optimized_encrypt_server.py <size_in_bytes> <data_rate_in_bps> <number_of_tests>
```
