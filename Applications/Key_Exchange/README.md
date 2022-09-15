This code base was used for extending dolphin with Key exchange.  
After key exchange, client sends data of various sizes at different rates with encryption and decryption.

In the "Client" directory:  
1. data_file.txt : It holds the data to be sent
2. refresh.py : It has various utility functions to conduct the experiment. The smartphone's bluetooth address needs to be manually set in this file in global field "BT_ADDR".
3. encrypt_client.py : It conducts the actual key exchange experiments. The server's phone number needs to be manually set in this file in global field "SERV_NO". Also, it requires pulseaudio sink name on client's linux machine which needs to be manually set in this file in global field "SINK_NAME".

A user needs to run encrypt_client.py with following paramters: 
```
python3 encrypt_client.py <data_file> <size_in_bytes> <data_rate_in_bps> <number_of_tests>
```

In the "Server" directory:
1. optimized_encrypt_server.py : It receives tweets from client and posts on behalf of client. Also, it requires pulseaudio sink name on server's linux machine which needs to be manually set in this file in global field "SINK_NAME".

A user needs to run encrypt_server.py with following paramters: 
```
python3 encrypt_server.py <size_in_bytes> <data_rate_in_bps> <number_of_tests>
```
