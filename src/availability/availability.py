import json
import logging

from requests.api import request
import boto3 
import requests
import os
from datetime import date
from botocore.exceptions import ClientError
from requests import RequestException
from boto3.dynamodb.conditions import Key, Attr
import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

cowin_url = os.getenv['appointment']
chat = os.getenv['chat']

def availablity():
    now = datetime.datetime.now() 
    now = now.strftime("%d-%m-%Y")    
    try:
        logger.info(f"Requesting {cowin_url}")
        res = requests.get(cowin_url+'&date='+now)
        logger.info(f"Request successful")
        json_response = res.json()
        reply = check(json_response)
        logger.info(f"reply constructed as {reply}")
        send_info(reply)
    except RequestException as e:
        logger.error(f"Cowin API Call Failed {e}")
    

def check(response):
    centers = response['centers']
    reply = []
    for i in centers:
        name = i['name']
        sessions = i['sessions']
        for s in sessions:
            min_age = int(s['min_age_limit'])
            dose_1 = int(s['available_capacity_dose1'])
            vaccine = s['vaccine']
            date = s['date']
            if min_age < 45 and dose_1 > 0:
                x = f"{dose_1} does of {vaccine} is available at {name} on {date} "
                reply.append(x)

    if len(reply>0):
        reply = "\n".join(reply)
    else:
        reply = "No Slots Are Available"
    return reply

def send_info(reply):
    data = {}
    data['message']=reply
    data['chat_id']=chat
    data = json.dumps(data)
    response = lambda_client.invoke(
        FunctionName="sendAppointmentDetails",
        InvocationType='Event',
        Payload=data
    )
    logger.info(f"Invoked sendAppointmentDetails lambda with response f{response}")
