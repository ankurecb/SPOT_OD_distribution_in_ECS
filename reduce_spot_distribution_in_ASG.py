#from __future__ import print_function
import boto3
#from urlparse import urlparse
import os
import base64
import json
from datetime import datetime
import time
import logging
from slack import WebClient
from slack.errors import SlackApiError


client_ASG = boto3.client('autoscaling')
ses_client = boto3.client('ses')

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

def send_mail(min_onDemand_percentage):
    try:
        dt = datetime.now()
        print("datetime = ", dt, dt.hour, dt.minute)
        if int(min_onDemand_percentage) > 9:
            if dt.hour == 3 and dt.minute > 9:
                print("Alert Min On demand percentange is more than 10")
                CHARSET = "utf-8"
                msg['Subject'] = "Alert !! Beauty -  Min On demand percentange is more than 10"
                try:
                    response = ses_client.send_raw_email(
                        Source="soruce-mail",
                        Destinations=["destination-mail"],
                        RawMessage={'Data': msg.as_string(),
                        }
                    )
                    print("Message id : ", response['MessageId'])
                    print("Message send successfully!")
                except Exception as e:
                    print("Error: ", e)
    except Exception as e:
        print(e)

def lambda_handler(event, context):

    # line = event['Records'][0]['Sns']['Message']
    # message = json.loads(line)
    # Ec2InstanceId = message['EC2InstanceId']
    # asgGroupName = message['AutoScalingGroupName']
    
    asgGroupNameList = os.environ['asgGroupNames'].split(",")
    disbabled_asgList = os.environ['disbabled_asg'].split(",")
    min_onDemand_percentage = os.environ['min_onDemand_percentage']
    
    send_mail(min_onDemand_percentage)
    
    count = 0
    response1 = asgClient.describe_auto_scaling_instances()
    
    for asgGroupName in asgGroupNameList:
        if asgGroupName  in disbabled_asgList:
            print("Ignore : ", asgGroupName)
        else:
            for res in response1['AutoScalingInstances']:
                print(res)
                if res['AutoScalingGroupName'] == asgGroupName and res['LifecycleState'] == 'InService':
                    count += 1
                    print(res['InstanceId'])
                    print(count)
            
            print("asgGroupName =", asgGroupName)
            
            
            response_describe = client_ASG.describe_auto_scaling_groups(
                AutoScalingGroupNames=[asgGroupName,],
            )
            
            ins_count = 0
            for ins in  response_describe['AutoScalingGroups']:
                ins_total = ins['Instances']
                print(ins_total)
                for i in ins_total:
                    if i['LifecycleState'] == 'InService':
                        ins_count += 1
                        print(ins_count)
                        print(i['InstanceId'])
            
            
            print("InstancesDistribution['OnDemandPercentageAboveBaseCapacity'] = ", response_describe['AutoScalingGroups'][0]['MixedInstancesPolicy']['InstancesDistribution']['OnDemandPercentageAboveBaseCapacity'])
            current_OnDemandPercentageAboveBaseCapacity = response_describe['AutoScalingGroups'][0]['MixedInstancesPolicy']['InstancesDistribution']['OnDemandPercentageAboveBaseCapacity']
            DesiredCapacity = response_describe['AutoScalingGroups'][0]['DesiredCapacity']
            
            print("current_OnDemandPercentageAboveBaseCapacity", current_OnDemandPercentageAboveBaseCapacity)
            print("DesiredCapacity", DesiredCapacity)
            
            next_OnDemandPercentageAboveBaseCapacity = current_OnDemandPercentageAboveBaseCapacity
            
            if current_OnDemandPercentageAboveBaseCapacity > int(min_onDemand_percentage) :
                if ins_count >= DesiredCapacity:
                    next_OnDemandPercentageAboveBaseCapacity = current_OnDemandPercentageAboveBaseCapacity - 10
                
                response = client_ASG.update_auto_scaling_group(
                    AutoScalingGroupName=asgGroupName,
            
                    MixedInstancesPolicy={
                        'InstancesDistribution': {
                            'OnDemandPercentageAboveBaseCapacity': next_OnDemandPercentageAboveBaseCapacity
                        }
                    },
                )
           
                
                slack_var = "*ASG_Group_Name* = " + '*{0}*'.format(asgGroupName) + "\n Instance_Running_count = " + str(ins_count) + "\n DesiredCapacity = " + str(DesiredCapacity) + "\n current_On_Demand_Percentage = " + str(current_OnDemandPercentageAboveBaseCapacity) + "\n Reduced to --> " + str(next_OnDemandPercentageAboveBaseCapacity)
                
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
            
            else:
                next_OnDemandPercentageAboveBaseCapacity 
                print("current_OnDemandPercentageAboveBaseCapacity is", current_OnDemandPercentageAboveBaseCapacity)
    
