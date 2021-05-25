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


def availablity():
    cowin_url = os.environ['appointment']
    now = datetime.datetime.now() 
    now = now.strftime("%d-%m-%Y")    
    try:
        final_url = cowin_url+'&date='+now
        logger.info(f"Requesting {final_url}")
        headers = {'user-agent': 'my-app/0.0.1'}
        res = requests.get(final_url,headers=headers)

        logger.info(f"Request successful {res}")
        json_response = res.json()
        reply = check(json_response)
        logger.info(f"reply constructed as {reply}")

        if reply["available"]:  
            send_info(reply["slots"])
        else:
            send_info("Nothing Available")
    except RequestException as e:
        logger.error(f"Cowin API Call Failed {e}")
        try:
            send_info("Call API Failed")
        except Exception as f:
            logger.error(f"Tragic Error {f}")
    

def check(response):
    centers = response['centers']
    reply = {
        "available" : False
    }
    available = []
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
                available.append(x)

    if len(available) > 0:
       reply["available"] = True
       reply["slots"] = "\n".join(available)

    return reply

def send_info(reply):
    chat = os.environ['chat']
    data = {}
    data['message']=reply
    data['chat_id']=chat
    data = json.dumps(data)
    lambda_client = boto3.client('lambda')
    response = lambda_client.invoke(
        FunctionName="bank-communication",
        InvocationType='Event',
        Payload=data
    )
    logger.info(f"Invoked bank-communication lambda with response f{response}")


def lambda_handler(event, context):
    availablity()