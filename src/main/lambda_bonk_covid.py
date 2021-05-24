import json
import logging
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

dynamodb = boto3.resource('dynamodb')

texts = ['/start','/stop']

class ResponseMessages():
    registered = ( "You've been succefully, registered. \n"
                   "Welcome to the path towards being vaccinated \n"
                   "You will now recieve notification whenever a vaccine is available at your pin-code. \n"
                   "To stop getting these alerts send `/stop` and to start again send `/start`"
    )
    already_re = "You are already registered."
    error_re = "Sorry, we couldn't register you. Please try again later."
    deregistered = "You have been successfully de-registered, to start again send `/start`."
    error_occured  = "I don't feel so good. An error has occured"
    default = "Hi, Bonk-Covid is primarily an alert bot and doesn't understand conversations. Thanks" 

reply = ResponseMessages()

def lambda_handler(event, context):
    logger.info(f"Event {event}")
    logger.info(f"#Event Body {event['body']} ")
    body = event['body']
    body = json.loads(body)

    try:
        process(body["message"])
    except:
        logger.error("Exception when invoking process")
        raise 
    
    return {
        'statusCode': 200
    }

def process(request): 
    try:
        logger.info(f"request: {request}")

        user_id = request['from']['id']
        chat_id = request['chat']['id']
        username = request['from']['first_name']
        message = request['text']
        
        logger.info(f"user_id {user_id}, chat_id {chat_id}, message {message}")

        result_msg = reply.default 
        if message.lower() in texts:
            method_name = "perform_"+message[1:].lower()
            result_msg = globals()[method_name](chat_id,user_id,username)
        
        send_reply(chat_id,result_msg)
        
    except:
        logger.error("exeception occured while trying to match message with function")
        raise

# if already exists skip and send different message else insert 
def perform_start(chat_id,user_id,username):
    now = datetime.datetime.now() 
    now = now.strftime("%d-%b-%Y %H:%M:%S.%f")    
    chats = dynamodb.Table("bonk_users")
    try:
        chats.put_item(Item={
            'chatid':str(chat_id),
            'userid':str(user_id),
            'username':str(username), 
            'active':True,
            'creation_time':now, 
            'updation_time':now
        },
        ConditionExpression='attribute_not_exists(chatid)'
        )
        logger.info("Successfully inserted the chatid in the db")
        return reply.registered
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            logger.info(f'already in table {e}')
            logger.info('checking if the user is disabled')
            result = chats.get_item(Key={'chatid':str(chat_id)})
            logging.info(f'Existing user is {result}')

            if not result['Item']['active']:
                logging.info("calling change status to activate")
                response = change_status(chat_id,True)
                logging.info(f'change status response {response}')
                if response: 
                     return reply.registered
                else:
                     return reply.error_re 
            else:
                logger.info(f'already registered {e}')
                return reply.already_re
        else:
            logger.error(f"Error while inserting into table Chats {e.response['Error']['Message']}")
    return reply.error_re


def perform_stop(chat_id,user_id,username):
    logging.info("calling change status to deactivate ")
    response = change_status(chat_id,False)
    logging.info(f'change status response {response}')
    if response:
        return reply.deregistered
    else:
        return reply.error_occured
    
def change_status(chat_id,status):
    now = datetime.datetime.now() 
    now = now.strftime("%d-%b-%Y %H:%M:%S.%f")    
    chats = dynamodb.Table("bonk_users")    
    try:
        chats.update_item(
            Key={
            'chatid': str(chat_id)
            },
            UpdateExpression='SET active = :newstatus,updation_time = :now',
            ExpressionAttributeValues={
            ':newstatus': status, 
            ':now': now
            }
        )
        return True
    except ClientError as e:
        logger.error(e.response['Error']['Message'])
    return False     

def send_reply(chat_id,message):
    accesscode = os.environ['accesscode']

    try:
        url = f"https://api.telegram.org/bot{accesscode}/sendMessage"
        logger.info(f"url formed is {url}")
        response = requests.post(url, data={'chat_id':chat_id,'text':message})
        logger.info(f"Successfully sent message! {message}")
    except RequestException as e:
        logger.error(f"Couldn't send reply {e}")