import boto3
from botocore.exceptions import ClientError
import json
import os

def lambda_handler(event, context):
    
    print('start function ')
    
    ec2 = boto3.client('ec2')

    regions = ec2.describe_regions()['Regions']
    regionList = [e['RegionName'] for e in regions]

    sg_with_public_access = dict()


    for region in regionList:
        print('getting sgs from region %s' % (region))
        ec2 = boto3.client('ec2',region)
        
        all_sg_response = ec2.describe_security_groups()
        print("all_sg_response")
        print(all_sg_response)
        for sg in all_sg_response['SecurityGroups']:
            sgId = sg['GroupId']
            vpcId = sg['VpcId']
            print('sgId %s' % (sgId))
            isDeleted = False
            try:
                response = ec2.delete_security_group(GroupId=sgId)
                print('Security Group %s Deleted' % (sgId))
                isDeleted = True
            except ClientError as e:
                print(e)
            if isDeleted == False:
                for ipPermission in sg['IpPermissions']:      
                    for ipRange in ipPermission['IpRanges']:
                        if ipRange['CidrIp'] == "0.0.0.0/0" :
                            if region in sg_with_public_access:
                                if sgId not in sg_with_public_access[region]:
                                    sg_with_public_access[region][sgId] = {"Ports":[]}
                            else:
                                sg_with_public_access[region] = {}
                                sg_with_public_access[region][sgId] = {"Ports":[]}

                            if ipPermission["IpProtocol"] == "-1":
                                sg_with_public_access[region][sgId]["Ports"].append("All")
                            elif "ToPort" in ipPermission and ipPermission["ToPort"] not in sg_with_public_access[region][sgId]["Ports"]:
                                sg_with_public_access[region][sgId]["Ports"].append(ipPermission['ToPort'])
                                
                            sg_with_public_access[region][sgId]["vpcId"] = vpcId

                    for ipRange in ipPermission['Ipv6Ranges']:
                        if ipRange['CidrIpv6'] == "::/0" :
                            if region in sg_with_public_access:
                                if sgId not in sg_with_public_access[region]:
                                    sg_with_public_access[region][sgId] = {"Ports":[]}
                            else:
                                sg_with_public_access[region] = {}
                                sg_with_public_access[region][sgId] = {"Ports":[]}

                            if ipPermission["IpProtocol"] == "-1":
                                sg_with_public_access[region][sgId]["Ports"].append("All")
                            elif "ToPort" in ipPermission and ipPermission["ToPort"] not in sg_with_public_access[region][sgId]["Ports"]:
                                sg_with_public_access[region][sgId]["Ports"].append(ipPermission['ToPort'])
                                
                            sg_with_public_access[region][sgId]["vpcId"] = vpcId

    print("sg_with_public_access")
    print(sg_with_public_access)

    new_sg_with_public_access = dict()
    
    htmlTable='<table><tr><th>REGION</th><th>SG ID</th><th>PORTS</th><th>INSTANCE ID</th><th>INSTANCE NAME(INSTANCE KEY NAME)</th><th>INSTANCE STATE</th></tr>';
    
    for key, value in sg_with_public_access.items():
        print('Key: %s' % (key))
        print('Value: %s'% (value))
        ec2 = boto3.client('ec2',key)
        response = ec2.describe_instances()
        
        result = {}
        result ['securityGroups'] = [];
        securityGroups = {}
        htmlTable += '<tr><td style="white-space: nowrap;">'+key+'</td></tr>'
        
        for sg in value:

            securityGroups[sg] = {};
            securityGroups[sg]['instances'] = []
            securityGroups[sg]['VpcId'] = value[sg]["vpcId"]
            securityGroups[sg]['Ports'] = value[sg]["Ports"]
            
            vpcId = value[sg]["vpcId"]
            niResponse = ec2.describe_network_interfaces(Filters=[
                {
                    'Name': 'vpc-id',
                    'Values': [value[sg]["vpcId"]]
                }
            ])
            
            if "NetworkInterfaces" in niResponse:
                if len(niResponse['NetworkInterfaces']) > 0:
                    for ni in niResponse['NetworkInterfaces']:
                        if "Groups" in ni:
                            for g in ni['Groups']:
                                if g['GroupId'] == sg:
                                    if "Attachment" in ni and "InstanceId" in ni['Attachment']:
                                        securityGroups[sg]['instances'].append(ni['Attachment']['InstanceId'])
            
        result ['securityGroups'] = securityGroups;
        new_sg_with_public_access[key] = result;
        
        for sg in securityGroups:
            htmlTable += '<tr><td></td><td style="white-space: nowrap;">'+sg+'</td><td align="center" style="white-space: nowrap;">'+str(value[sg]["Ports"])+'</td><td></td><td></td><td></td></tr>'
            if "instances" in securityGroups[sg]:
                for instanceId in securityGroups[sg]['instances']:
                    instanceResponse = ec2.describe_instances(InstanceIds=[instanceId])
                    i = instanceResponse['Reservations'][0]['Instances'][0]
                    
                    keyName = ""
                    if "KeyName" in i:
                        keyName = i['KeyName'].strip()
                    
                    filtered_tags = [t for t in i['Tags'] if t['Key'] == "Name"]
                    name = ""
                    if len(filtered_tags) > 0:
                        name = filtered_tags[0]['Value'].strip()
                    state = i['State']['Name'].strip()
                    
                    htmlTable += '<tr><td></td><td></td><td></td><td style="white-space: nowrap;">'+instanceId+'</td><td style="white-space: nowrap;">'+name+'( '+keyName+' )</td><td style="white-space: nowrap;">'+state+'</td></tr>'

    
    print("new_sg_with_public_access")                    
    print(new_sg_with_public_access)

    htmlTable += '</table>'
    ses_client = boto3.client('ses', 'eu-west-2')
    
    response = ses_client.send_email(
        Source=os.environ.get('FROM_EMAIL_ADDRESS'),
        Destination={
            'ToAddresses': os.environ.get('TO_EMAIL_ADDRESSES').strip('][').split(', ')
        },
        Message={
            'Subject': {
                'Data': 'SGs with public access',
                'Charset': 'utf-8'
            },
            'Body': {
                'Html': {
                    'Data': htmlTable
                }
            }
        }
    )
    
    print(response)
    
    return {
        'statusCode': 200
    }
