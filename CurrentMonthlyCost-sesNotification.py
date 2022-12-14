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



now = datetime.now()
year = now.year
month = now.month

START_DATE = f"{year}-{month:02d}-01"
#print(START_DATE)
date_plus_one_month = now + timedelta(weeks=4)
END_DATE = date_plus_one_month.strftime("%Y-%m-01")
#print(END_DATE)



def lambda_handler(event, context):
    deneme = dict()
    
    # Create an AWS Cost Explorer client
    client = boto3.client('ce')

    # Get the current month
    current_month = datetime.now().strftime('%Y-%m')

    # Get the cost and usage for the current month
    response = client.get_cost_and_usage(
        TimePeriod={
            'Start': START_DATE,
            'End': END_DATE
        },
        Granularity='MONTHLY',
        Metrics=['BlendedCost']
    )

    # Get the total cost for the current month
    total_cost = "Current-Month-Costs : " + format(float(response['ResultsByTime'][0]['Total']['BlendedCost']['Amount'].split("$")[0]), '.2f') + "$"

    
    #stats = dict()
    #send_format = ""
    #lambda_handler.send_format = dict()
    
    htmlTable='<table><tr><th>REGION</th><th>INSTANCE NAME</th><th>CPUUtilization</th><th>NetworkIn</th><th>NetworkOut</th></tr>';
    
    for region in regionList:
        ec2 = boto3.resource('ec2',region)

        filters = [{
                'Name': 'instance-state-name',
                'Values': ['running']
            },
        ]
        instances = ec2.instances.filter(Filters=filters)
        RunningInstances = [instance.id for instance in instances]
        #htmlTable += '<tr><td style="white-space: nowrap;">'+region+'</td></tr>'
        for filteredRunningInstances in RunningInstances:
            
            if filteredRunningInstances != []:
                #print(filteredRunningInstances,',',region)


                cloudwatch = boto3.client('cloudwatch',region)
        
                stats = cloudwatch.get_metric_statistics(
                    Namespace='AWS/EC2',
                    MetricName='CPUUtilization',
                    StartTime=datetime.now() + timedelta(days = -3),
                    EndTime=datetime.now(),
                    Statistics=['Maximum'],
                    Period=259200,
                    Dimensions=[
                        {
                            'Name': 'InstanceId',
                            'Value': filteredRunningInstances
                        },
                    ],
                )
                
                stats2 = cloudwatch.get_metric_statistics(
                    Namespace='AWS/EC2',
                    MetricName='NetworkIn',
                    StartTime=datetime.now() + timedelta(days = -3),
                    EndTime=datetime.now(),
                    Statistics=['Maximum'],
                    Period=259200,
                    #Unit='Megabytes',
                    Dimensions=[
                        {
                            'Name': 'InstanceId',
                            'Value': filteredRunningInstances
                        },
                    ],
                )
                
                stats3 = cloudwatch.get_metric_statistics(
                    Namespace='AWS/EC2',
                    MetricName='NetworkOut',
                    StartTime=datetime.now() + timedelta(days = -3),
                    EndTime=datetime.now(),
                    Statistics=['Maximum'],
                    Period=259200,
                    #Unit='Bytes',
                    Dimensions=[
                        {
                            'Name': 'InstanceId',
                            'Value': filteredRunningInstances
                        },
                    ],
                )
                
                
    #htmlTable='<table><tr><th>REGION</th><th>INSTANCE NAME(INSTANCE KEY NAME)</th><th>CPUUtilization</th><th>NetworkIn</th><th>NetworkOut</th></tr>';
                
                #deneme = [filteredRunningInstances,  region,  stats["Label"], stats["Datapoints"],  stats2["Label"], stats2["Datapoints"],  stats3["Label"], stats3["Datapoints"]]
                deneme[filteredRunningInstances] = {};
                deneme[filteredRunningInstances]['region'] = region;
                
                deneme[filteredRunningInstances]['CPU'] = {};
                deneme[filteredRunningInstances]['CPU']['Label'] = stats["Label"];
                deneme[filteredRunningInstances]['CPU']['Datapoints'] = stats["Datapoints"];
                #deneme[filteredRunningInstances]['CPU']['Datapoints'][0]['Maximum'][1] = stats["Maximum"];
                
                deneme[filteredRunningInstances]['NetworkIn'] = {}
                deneme[filteredRunningInstances]['NetworkIn']['Label'] = stats2["Label"];
                deneme[filteredRunningInstances]['NetworkIn']['Datapoints'] = stats2["Datapoints"];
                
                deneme[filteredRunningInstances]['NetworkOut'] = {}
                deneme[filteredRunningInstances]['NetworkOut']['Label'] = stats3["Label"];
                deneme[filteredRunningInstances]['NetworkOut']['Datapoints'] = stats3["Datapoints"];
                
                
                htmlTable += '<tr><td style="white-space: nowrap;">'+region+'</td></tr>';
                htmlTable += '<tr><td></td><td style="white-space: nowrap;">'+filteredRunningInstances+'</td><td></td><td></td><td></td></tr>'
                htmlTable += '<tr><td></td><td></td><td style="white-space: nowrap;">'+str(stats["Datapoints"])+'</td><td align="center" style="white-space: nowrap;">'+str(stats2["Datapoints"])+'</td><td align="center" style="white-space: nowrap;">'+str(stats3["Datapoints"])+'</td></tr>'
                
    #htmlTable='<table><tr><th>REGION</th><th>INSTANCE NAME(INSTANCE KEY NAME)</th><th>CPUUtilization</th><th>NetworkIn</th><th>NetworkOut</th></tr>';
            
    print(json.dumps(deneme, indent=2, default=str))
    print("sending email")
    
    #test = json2html.convert(json = deneme)
    #print(test)
    htmlTable += '</table>'
    
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
                'Html': {
                    'Data': total_cost
                }
            }
        }
    )