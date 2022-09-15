This code base was used for extending dolphin with email support. It assumes the user to have a gmail account.  
Additionaly, user also need to enable SMTP support on its Gmail account which can done in consultation with this official google support link : https://support.google.com/mail/answer/7126229?hl=en#zippy=%2Cstep-check-that-imap-is-turned-on%2Cstep-change-smtp-other-settings-in-your-email-client.  

In the "Client" directory:  
1. data_file.txt : It holds the data to be sent
2. refresh.py : It has various utility functions to conduct the experiment. The smartphone's bluetooth address needs to be manually set in this file in global field "BT_ADDR".
3. optimized_encrypt_client.py : It conducts the actual emailing experiments as client sending email contents to server. The server's phone number needs to be manually set in this file in global field "SERV_NO". Also, it requires pulseaudio sink name on client's linux machine which needs to be manually set in this file in global field "SINK_NAME".

A user needs to run optimized_encrypt_client.py with following paramters:
```
python3 optimized_encrypt_client.py <data_file> <size_in_bytes> <data_rate_in_bps> <number_of_tests>
```

In the "Server" directory:
1. refresh.py : It has various utility functions to conduct the experiment. The smartphone's bluetooth address needs to be manually set in this file in global field "BT_ADDR".
2. optimized_encrypt_server.py : It receives email contents from client and posts on behalf of client. Also, it requires pulseaudio sink name on server's linux machine which needs to be manually set in this file in global field "SINK_NAME".

A user needs to run optimized_encrypt_server.py with following paramters: 
```
python3 optimized_encrypt_server.py <size_in_bytes> <data_rate_in_bps> <number_of_tests>
```
