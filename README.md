# Python Script to automatically fetch and reply to Datacenter Abuse reports while checking the users on WHMCS

Currenly only one datacenter provider "Quadranet" is added here

The script was created in a very short time, and I am just learning, If you find any issues, or have any suggestions, feel free to let me know

## Run the main program (browser) by
```
python3 main.py
```
## Run the WHMCS_Ticket python script on docker by
```
sudo docker build -t "whmcs_ticket" . && sudo docker run -d -p 5000:5000 "whmcs_ticket"
```
## Prepare environment for main script
```
sudo apt install python3-pip
pip3 install -r requirements.txt
```