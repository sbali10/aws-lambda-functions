from warnings import resetwarnings
import boto3
import logging
from datetime import datetime, timedelta
from boto3.resources.model import ResponseResource
from botocore.exceptions import ClientError
import json
from pprint import pprint
import os
import sys

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ec2 = boto3.client('ec2')
regions = ec2.describe_regions()['Regions']
regionList = [e['RegionName'] for e in regions]

def lambda_handler(event, context):
    
    #stats = dict()
    #k = dict()

    for region in regionList:
        ec2 = boto3.resource('ec2',region)

        filters = [{
                'Name': 'instance-state-name',
                'Values': ['running']
            },
        ]
        instances = ec2.instances.filter(Filters=filters)
        RunningInstances = [instance.id for instance in instances]
        for filteredRunningInstances in RunningInstances:
            if filteredRunningInstances != []:
                #print(filteredRunningInstances,',',region)



                cloudwatch = boto3.client('cloudwatch',region)
        
                stats = cloudwatch.get_metric_statistics(
                    Namespace='AWS/EC2',
                    MetricName='CPUUtilization',
                    StartTime=datetime.now() + timedelta(minutes = -180),
                    EndTime=datetime.now(),
                    Statistics=['Maximum'],
                    Period=9600,
                    Dimensions=[
                        {
                            'Name': 'InstanceId',
                            'Value': filteredRunningInstances
                        },
                    ],
                )
                
                stats2 = cloudwatch.get_metric_statistics(
                    Namespace='AWS/EC2',
                    MetricName='NetworkPacketsIn',
                    StartTime=datetime.now() + timedelta(minutes = -10),
                    EndTime=datetime.now(),
                    Statistics=['Average'],
                    Period=60,
                    Dimensions=[
                        {
                            'Name': 'InstanceId',
                            'Value': filteredRunningInstances
                        },
                    ],
                )
                stats3 = cloudwatch.get_metric_statistics(
                    Namespace='AWS/EC2',
                    MetricName='NetworkPacketsOut',
                    StartTime=datetime.now() + timedelta(minutes = -10),
                    EndTime=datetime.now(),
                    Statistics=['Average'],
                    Period=60,
                    Dimensions=[
                        {
                            'Name': 'InstanceId',
                            'Value': filteredRunningInstances
                        },
                    ],
                )
                
                
                
                
                deneme = [filteredRunningInstances,',', region, ',', stats["Label"], stats["Datapoints"], ',', stats2["Label"], stats2["Datapoints"], ',',stats3["Label"], stats3["Datapoints"]]
               
                
                
            
                ses_client = boto3.client('ses', 'eu-west-2')
                rsp = ses_client.send_email(
                    Source=os.environ.get('FROM_EMAIL_ADDRESS'),
                    Destination={
                        'ToAddresses': os.environ.get('TO_EMAIL_ADDRESSES').strip('][').split(', ')
                    },
                    Message={
                        'Subject': {
                            'Data': 'Running EC2 InstanceDetails',
                            'Charset': 'utf-8'
                        },
                        'Body': {
                            'Text': {
                                'Data': json.dumps(deneme, indent=2, default=str),
                                'Charset': 'utf-8'
                            }
                        }
                    }
                )
