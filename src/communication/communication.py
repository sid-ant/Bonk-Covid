import json
import logging
import requests
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

url = os.environ['url']

def lambda_handler(event, context):
    logger.info(f"sendAppointmentDetails Recived Event as {event}")
    chat_id = event["chat_id"]
    msg = event["message"]
    send_message(chat_id,msg)


def send_message(chat_id,message):
    body = {
        "chat_id":chat_id, 
        "text":message
    }
    logging.info(f"Constructed SendMessage Request '{body}")
    response = requests.post(url,data=body)
    logging.info(f"Response {response}")
    json_response = response.json()
    logging.info(f"SendMessage Respose {json_response}")
        
    if not json_response['ok']:
        logging.error(f"SendMessage failed")
    

