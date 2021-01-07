'''
Description: Error Declare
Author: Chandler Lu
Date: 2021-01-07 17:14:36
LastEditTime: 2021-01-07 17:15:02
'''
import sys


def declare_network_error():
    print('Network connection refused!', end='')
    sys.exit(0)


def declare_file_error():
    sys.exit(0)
