import boto3
import time

from datetime import datetime, timedelta
from operator import itemgetter


class InstanceManager:

    def __init__(self):

        self.cw = boto3.client('cloudwatch')
        self.ec2 = boto3.client('ec2')
        self.cd = boto3.client('codedeploy')
        self.elb = boto3.client('elbv2')

        self.user_app_tag = 'ece1779-a2'
        self.image_id = 'ami-baf632ac'
        self.instance_type = 't2.small'
        self.key_pair = 'ece1779'
        self.security_group = ['launch-wizard-2']
        self.tag_specification = [{
            'ResourceType': 'instance',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': self.user_app_tag
                }]
        }]
        self.monitoring = {'Enabled': True}
        self.tag_placement = {'AvailabilityZone': 'us-east-1a'}

    def launch_instance(self, k=1):
        response = self.ec2.run_instances(ImageId=self.image_id,
                                          InstanceType=self.instance_type,
                                          KeyName=self.key_pair,
                                          MinCount=1,
                                          MaxCount=k,
                                          SecurityGroups=self.security_group,
                                          TagSpecifications=self.tag_specification,
                                          Monitoring=self.monitoring,
                                          Placement=self.tag_placement)
        return response['Instances']

    def terminate_instance(self, instance_ids):
        assert all(isinstance(instance_id, str)
                   for instance_id in instance_ids)
        self.ec2.terminate_instances(InstanceIds=instance_ids, DryRun=False)
        return instance_ids

    def get_instance_status(self, instance_ids):
        response = self.ec2.describe_instance_status(InstanceIds=instance_ids)
        return [{"id": instance_status['InstanceId'], "state":instance_status['InstanceState']}
                for instance_status in response['InstanceStatuses']]

    def get_instances(self, live_only=False):
        response = self.ec2.describe_instances()

        if live_only:
            return list(filter(lambda x: x['State']['Name'] in ['pending', 'running'], response['Reservations'][0]['Instances']))

        return response['Reservations'][0]['Instances']

    def get_cpu_utilization(self):
        statistics = 'Average'
        response = self.cw.get_metric_statistics(
            Period=1 * 60,
            StartTime=datetime.utcnow() - timedelta(seconds=30 * 60),
            EndTime=datetime.utcnow() - timedelta(seconds=0 * 60),
            MetricName='CPUUtilization',
            Namespace='AWS/EC2',  # Unit='Percent',
            Statistics=[statistics]
        )

        return self._data_conversion_helper(response, statistics)

    def get_instance_inbound_rate(self):
        statistics = 'Sum'
        response = self.cw.get_metric_statistics(
            Period=1 * 60,
            StartTime=datetime.utcnow() - timedelta(seconds=30 * 60),
            EndTime=datetime.utcnow() - timedelta(seconds=0 * 60),
            MetricName='NetworkIn',
            Namespace='AWS/EC2',  # Unit='Percent',
            Statistics=[statistics]
        )
        return self._data_conversion_helper(response, statistics)

    def register_instances_elb(self, instance_ids):
        pass

    def unregister_instances_elb(self, instance_ids):
        pass

    def deploy_instances(self, instance_ids):
        return instance_ids

    def _data_conversion_helper(self, response, statistics):
        res = [[point['Timestamp'].hour+point['Timestamp'].minute/60,
                point[statistics]] for point in response['Datapoints']]
        return sorted(res, key=itemgetter(0))


if __name__ == "__main__":
    manager = InstanceManager()
    instances = manager.get_instances()
    cpu_usage = manager.get_instance_inbound_rate()
    print(cpu_usage)