from __future__ import print_function
import boto3
#from urlparse import urlparse
import base64
import json
import datetime
import time
import logging
from slack import WebClient
from slack.errors import SlackApiError


client_ASG = boto3.client('autoscaling')

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Establish boto3 session
session = boto3.session.Session()
logger.debug("Session is in region %s ", session.region_name)

ec2Client = session.client(service_name='ec2')
ecsClient = session.client(service_name='ecs')
asgClient = session.client('autoscaling')
snsClient = session.client('sns')
lambdaClient = session.client('lambda')

def lambda_handler(event, context):


    line = event['Records'][0]['Sns']['Message']
    message = json.loads(line)
    Ec2InstanceId = message['EC2InstanceId']
    asgGroupName = message['AutoScalingGroupName']
    
    print("asgGroupName =", asgGroupName)
    
    response_describe = client_ASG.describe_auto_scaling_groups(
        AutoScalingGroupNames=[asgGroupName,],
    )
    
    
    print("InstancesDistribution['OnDemandPercentageAboveBaseCapacity'] = ", response_describe['AutoScalingGroups'][0]['MixedInstancesPolicy']['InstancesDistribution']['OnDemandPercentageAboveBaseCapacity'])
    current_OnDemandPercentageAboveBaseCapacity = response_describe['AutoScalingGroups'][0]['MixedInstancesPolicy']['InstancesDistribution']['OnDemandPercentageAboveBaseCapacity']
    
    
    if current_OnDemandPercentageAboveBaseCapacity < 81:
        next_OnDemandPercentageAboveBaseCapacity = current_OnDemandPercentageAboveBaseCapacity + 10
    
        for res in response_describe['AutoScalingGroups']:
            print("DesiredCapacity=",res['DesiredCapacity'])
    
        response = client_ASG.update_auto_scaling_group(
            AutoScalingGroupName=asgGroupName,
        
            MixedInstancesPolicy={
                'InstancesDistribution': {
                    'OnDemandPercentageAboveBaseCapacity': next_OnDemandPercentageAboveBaseCapacity
                }
            },
        )
        slack_var = "*ASG_Group_Name* = " + "*{0}*".format(asgGroupName) + "\n current_On_Demand_Percentage = " + str(current_OnDemandPercentageAboveBaseCapacity) + "\n Increased to --> " + str(next_OnDemandPercentageAboveBaseCapacity)
        
        client = WebClient(token='your-token')
    
        try:
            response = client.chat_postMessage(
                channel='#channel-name',
                text=slack_var)
            print(response["message"]["text"])
            #assert response["message"]["text"] == slack_var
        except SlackApiError as e:
            # You will get a SlackApiError if "ok" is False
            assert e.response["ok"] is False
            assert e.response["error"]  # str like 'invalid_auth', 'channel_not_found'
            print(f"Got an error: {e.response['error']}")
            
