from warnings import resetwarnings
import boto3
import logging
from datetime import datetime
from datetime import timedelta
from botocore.exceptions import ClientError
import json
import os

#setup simple logging for INFO
logger = logging.getLogger()
logger.setLevel(logging.INFO)

#define the connection
# ec2 = boto3.resource('ec2')
# cw = boto3.client('cloudwatch')

def lambda_handler(event, context):
    #ec2 = boto3.resource('ec2')
    cw = boto3.client('cloudwatch')
    ec2 = boto3.client('ec2')


    regions = ec2.describe_regions()['Regions']
    regionList = [e['RegionName'] for e in regions]


    for region in regionList:
        #ec2 = boto3.resource('ec2',region)
        cw = boto3.resource('cloudwatch',region)

        #response = boto3.client('cloudwatch',region)
        response = cw.get_metric_statistics(
            Namespace = name_space,
            MetricName = metric_name,
            Dimensions = dimensions_values,
            StartTime = datetime.now() + timedelta(days = -1),
            EndTime = datetime.now(),
            Period = 86400,
            Statistics = [statistic]

        )
        print(json.dumps(response, indent=2))
  






####SEND MAIL

    # ses_client = boto3.client('ses', 'eu-west-2')

    # response = ses_client.send_email(
    #     Source= "no-reply@aws-admin.ti-dev.siemens.cloud",
    #     Destination={
    #         'ToAddresses': os.environ.get('serhat.bali@siemens.com').strip('][').split(', ')
    #     },
    #     Message={
    #         'Subject': {
    #             'Data': 'sb-test',
    #             'Charset': 'utf-8'
    #         },
    #         'Body': {
    #             'Text': {
    #                 'Data': print(json.dumps(all_sg_response, indent=2)),
    #                 'Charset': 'utf-8'
    #             }
    #         }
    #     }
    # )

    # print(response)

    # return {
    #     'statusCode': 200
    # }

