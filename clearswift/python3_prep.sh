#!/usr/bin/bash

echo "Installing Python 3.6"
sudo yum install -y python36
echo "Installing setup tools"
sudo yum install -y python36-pip python36-wheel
sudo python3 -m pip install --upgrade pip
echo "Installing needed modules"
sudo python3 -m pip install argparse lxml uuid

