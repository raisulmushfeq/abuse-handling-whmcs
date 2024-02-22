FROM python
WORKDIR /home/
COPY ./whmcs_ticket.py ./
COPY ./requirements.txt ./
RUN pip install -r requirements.txt
CMD [ "python3", "./whmcs_ticket.py" ]
