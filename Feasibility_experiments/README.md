The code base in this directory was used to run the feasibility experiments for varying data sizes and data rates.  
In the experiments, we had 2 sides: Sender and Receiver.

Sender:  
It places a call and sends a certain amount of data at a certain data rate (in bps).

In "Sender" directory, there are 3 files:
1. data_file.txt : It holds the data to be sent
2. refresh.py : It holds various utility functions to conduct the experiment. The smartphone's bluetooth address needs to be manually set in this file in global field "BT_ADDR".
3. sending_test.py : This file conducts the main experiment of sending data. The receiver's phone number needs to be manually set in this file in global field "RECV_NO".

A user needs to run sending_test.py with following paramters: python3 sending_test.py <data_file> <size_in_bytes> <data_rate_in_bps> <number_of_tests>

Receiver:  
It waits to receive the call, receive data from sender and computes the error.

In "Receiver" directory, there are 3 files:
1. data_file.txt : This should be same as that in "Sender" directory to compute the errors.
2. test_call.py : It conducts the experiment by receiving data from sender multiple times and saves the received data in directories with naming format "data_<data_rate_in_bps>_<size_of_data>". Example of such a directory is given.
3. test_error.py : It computes the error on received data and assumes the existence of directories with naming format "data_<data_rate_in_bps>_<size_of_data>".


A user needs to run test_call.py with following paramters: python3 test_call.py <size_in_bytes> <data_rate_in_bps> <number_of_tests>  
Also, user needs to run test_error.py with following parameters : python3 test_error.py <root_directory>  
root_directory is the directory where directories with given naming convention resides. If test_call.py and test_error.py are placed in same directory, then command would be : python3 test_error.py .
