import os
import boto3

from colorama import Fore
from colorama import Style


class Aws:
    def __init__(self, region, profile, product, env):
        if not region:
            region = os.getenv('AWS_REGION')
        if not profile:
            profile = os.getenv('AWS_PROFILE')
        if not product:
            product = os.getenv('PRODUCT')
        if not env:
            env = os.getenv('ENV')

        self.region = region
        self.profile = profile
        self.product = product
        self.env = env

        session = boto3.Session(profile_name=profile)
        self.ssm = session.client('ssm')
        self.asg = session.client('autoscaling')

        print(f'{Fore.BLUE}PRODUCT{Style.RESET_ALL} : {Fore.GREEN}{self.product}{Style.RESET_ALL} / '
              + f'{Fore.BLUE}ENVIRONMENT{Style.RESET_ALL} : {Fore.GREEN}{self.env}{Style.RESET_ALL}{os.linesep}')

    def __path(self):
        return f'/{self.product}/{self.env}/'

    def __path_with_name(self, name):
        return f'{self.__path()}{name}'

    def __path_without_name(self, name):
        return name.replace(self.__path(), '')

    def __param_to_hash(self, parameter):
        return {
            'name': self.__path_without_name(parameter['Name']),
            'type': parameter['Type'],
            'value': parameter['Value'],
            'version': parameter['Version'],
            'arn': parameter['ARN']
        }

    def __asg_to_hash(self, asg):
        return {
            'name': asg['AutoScalingGroupName'],
            'min': asg['MinSize'],
            'max': asg['MaxSize'],
            'desired': asg['DesiredCapacity'],
            'azs': asg['AvailabilityZones']
        }

    def __asg_in_env(self, asg):
        """
        Determine if a returned autoscaling group is on our environment
        :param asg: The autoscaling group hash
        :return: true if it is, false otherwise
        """
        our_env = False
        our_product = False

        for tag in asg['Tags']:
            if tag['Key'] == 'Environment' and tag['Value'] == self.env:
                our_env = True
            if tag['Key'] == 'Product' and tag['Value'] == self.product:
                our_product = True

        return our_env and our_product

    def scale_asg(self, asg, min, max, desired):
        """
        Scale an environment's autoscaling group up or down
        :param asg: The name of the autoscaling group to scale
        :param min: The minimum number of nodes to have in service
        :param max: The maximum number of nodes to have in service
        :param desired: The desired number of nodes to have in service
        :return:
        """
        try:
            self.asg.update_auto_scaling_group(AutoScalingGroupName=asg, MinSize=min, MaxSize=max,
                                               DesiredCapacity=desired)
        except Exception as e:
            print(e)

    def get_asgs(self):
        """
        Retrieve a list of autoscaling groups associated with this product/environment
        :return:
        """
        next_token = None
        asgs = []

        try:
            while True:
                if next_token:
                    response = self.asg.describe_auto_scaling_groups(NextToken=next_token)
                else:
                    response = self.asg.describe_auto_scaling_groups()

                if 'AutoScalingGroups' in response:
                    for asg in response['AutoScalingGroups']:
                        if self.__asg_in_env(asg):
                            asgs.append(self.__asg_to_hash(asg))

                if 'NextToken' in response:
                    next_token = response['NextToken']
                else:
                    break

            return asgs
        except Exception as e:
            print(e)
            return {}

    def show_k8s_dashboard(self):
        """
        Show an environment's Kubernetes cluster dashboard
        :return:
        """
        pass

    def set_secret(self, name, value, encrypt):
        """
        Set a secret's value
        :param encrypt: Set to True to encrypt the secret
        :param name: The name of the secret to set
        :param value: The value to set the secret to
        :return:
        """
        try:
            self.ssm.put_parameter(Name=f'{self.__path_with_name(name)}', Value=value, Overwrite=True,
                                   Type='SecureString' if encrypt else 'String')
        except Exception as e:
            print(e)

    def delete_secret(self, name):
        """
        Delete a secret
        :param name: The name of the secret to delete
        :return:
        """
        try:
            self.ssm.delete_parameter(Name=f'{self.__path_with_name(name)}')
        except Exception as e:
            print(e)

    def get_secret(self, name):
        """
        Get a single secret
        :param name: The name of the secret to retrieve
        :return: the secrets details
        """
        try:
            response = self.ssm.get_parameter(Name=f'{self.__path_with_name(name)}', WithDecryption=True)
            if 'Parameter' in response:
                parameter = response['Parameter']
                return self.__param_to_hash(parameter)
            else:
                return {}
        except Exception as e:
            print(e)
            return {}

    def get_all_secrets(self):
        """
        Get all secrets in an environment
        :return: the list of secrets in an environment. these are stored in SSM parameters
        """
        secrets = []
        next_token = None

        try:
            while True:
                if next_token:
                    response = self.ssm.get_parameters_by_path(Path=f'{self.__path()}', Recursive=True,
                                                               WithDecryption=True,
                                                               NextToken=next_token)
                else:
                    response = self.ssm.get_parameters_by_path(Path=f'{self.__path()}', Recursive=True,
                                                               WithDecryption=True)

                for parameter in response['Parameters']:
                    secrets.append(self.__param_to_hash(parameter))

                if 'NextToken' in response:
                    next_token = response['NextToken']
                else:
                    break
        except Exception as e:
            print(e)

        return secrets
