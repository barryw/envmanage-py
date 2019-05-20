import os
import click
from click import UsageError, ClickException

from aws import Aws
from colorama import Fore
from colorama import Style
from dateutil import tz
import time

from kubernetes import Kubernetes


@click.group()
@click.option('-p', '--product', default=os.getenv('PRODUCT'), envvar='PRODUCT', help='The product to operate on',
              show_default=True)
@click.option('-e', '--env', default=os.getenv('ENV'), envvar='ENV', help='The environment to operate on',
              show_default=True)
@click.option('-b', '--profile', default=os.getenv('AWS_PROFILE'), envvar='AWS_PROFILE', help='The AWS profile to use ',
              show_default=True)
@click.option('-r', '--region', default=os.getenv('AWS_REGION'), envvar='AWS_REGION', help='The AWS region to use',
              show_default=True)
@click.option('-f', '--format', default='text', envvar='ENVMANAGE_FORMAT', help='The format to output in',
              type=click.Choice(['text', 'json']), show_default=True)
@click.option('-k', '--kubeconfig', envvar='KUBECONFIG', help='The path to your kube config file.')
@click.pass_context
def cli(ctx, product, env, profile, region, format, kubeconfig):
    """
    This CLI can be used to manage products and environments conforming to a set of standards. The deployments should
    have set the following tags on their resources:

    Product: The name of the deployed product (eg. my-awesome-product)
    Environment: The discrete environment for the product (eg. dev, qa, stg, prod)

    To work with your products and environments, you will either need to set some environment variables or pass in some
    command line switches. The easiest way is to create a set of shell scripts that you can source in to set the
    appropriate environment variables for a product/environment. For example, you could have a shell script named
    foo-dev.sh containing the following:

    #!/bin/bash

    export PRODUCT=foo\n
    export ENV=dev\n
    export AWS_PROFILE=foo-dev-profile (this is the profile name from ~/.aws/credentials)\n
    export AWS_REGION=us-west-2\n
    export KUBECONFIG=/home/joesmith/Git/Phoenix/terraform/products/foo/kubeconfig_v2-dev\n

    Source this script in before working with this CLI, and all commands executed will take effect against the product /
    environment specified by the environment variables.

    If your product uses Kubernetes, make sure that KUBECONFIG is set to the location of your environment's kubeconfig
    file. This will allow you to run the show-dashboard command to open the Kubernetes dashboard for your product.
    """
    aws = Aws(region, profile, product, env, format)
    kube = Kubernetes(kubeconfig)
    ctx.obj['AWS'] = aws
    ctx.obj['FORMAT'] = format
    ctx.obj['KUBE'] = kube


@cli.command(help="Show a list of all secrets for an environment")
@click.pass_context
def list_secrets(ctx):
    aws = ctx.obj['AWS']
    secrets = aws.get_all_secrets()
    if ctx.obj['FORMAT'] == 'json':
        print(secrets)
    else:
        for secret in secrets:
            print(
                f"{Fore.GREEN}{secret['name']}{Style.RESET_ALL} ({Fore.LIGHTBLUE_EX}{secret['type']}{Style.RESET_ALL})")


@cli.command(help="Display a secret's value")
@click.option('-n', '--name', help='The name of the secret to display', required=True)
@click.pass_context
def show_secret(ctx, name):
    aws = ctx.obj['AWS']
    secret = aws.get_secret(name)

    if secret == {}:
        raise ClickException("No parameter with that name was found.")

    if ctx.obj['FORMAT'] == 'json':
        print(secret)
    else:
        print(f"{Fore.GREEN}{secret['name']}{Style.RESET_ALL} ({Fore.LIGHTBLUE_EX}{secret['type']}{Style.RESET_ALL}) "
              + f"= {Fore.LIGHTRED_EX}{secret['value']}{Style.RESET_ALL}")


@cli.command(help="Set a secret's value")
@click.option('-n', '--name', help='The name of the secret to set', required=True)
@click.option('-v', '--value', help='The value to set the secret to', required=True)
@click.option('-encrypt/-no-encrypt', is_flag=True, help='Whether to create an encrypted secret', default=True)
@click.pass_context
def set_secret(ctx, name, value, encrypt):
    aws = ctx.obj['AWS']
    aws.set_secret(name, value, encrypt)


@cli.command(help='Delete a secret')
@click.option('-n', '--name', help='The name of the secret to delete', required=True)
@click.pass_context
def delete_secret(ctx, name):
    aws = ctx.obj['AWS']
    aws.delete_secret(name)


@cli.command(help="Show the Kubernetes dashboard for this environment (requires $KUBECONFIG to be set and pointing at "
                  + "your environment's kubeconfig file)")
@click.pass_context
def show_dashboard(ctx):
    kube = ctx.obj['KUBE']
    if not kube.kubeconfig:
        raise UsageError("You need to either set your KUBECONFIG env var or use the -k option to the path to your "
                         + "product/environment's kube config")

    kube.show_dashboard()


@cli.command(help="Scale an environment up")
@click.option('-a', '--asg', help='The name of the autoscaling group to scale.', required=True)
@click.option('--min', help='The min value for the autoscaling group', default=1)
@click.option('--max', help='The max value for the autoscaling group', default=1)
@click.option('-d', '--desired', help='The desired value for the autoscaling group', default=1)
@click.pass_context
def scale_up(ctx, asg, min, max, desired):
    aws = ctx.obj['AWS']
    aws.scale_asg(asg, min, max, desired)


@cli.command(help="Scale an environment down")
@click.option('-a', '--asg', help='The name of the autoscaling group to scale.', required=True)
@click.option('--min', help='The min value for the autoscaling group', default=0)
@click.option('--max', help='The max value for the autoscaling group', default=0)
@click.option('-d', '--desired', help='The desired value for the autoscaling group', default=0)
@click.pass_context
def scale_down(ctx, asg, min, max, desired):
    aws = ctx.obj['AWS']
    aws.scale_asg(asg, min, max, desired)


@cli.command(help="Display information on the environment's instances and autoscaling groups")
@click.pass_context
def show_env(ctx):
    aws = ctx.obj['AWS']
    instances = aws.get_instances()
    asgs = aws.get_asgs()

    if ctx.obj['FORMAT'] == 'json':
        struct = {
            'instances': instances,
            'asgs': asgs
        }
        print(struct)
    else:
        zone = tz.gettz(time.tzname[0])
        print(f'{Fore.GREEN}Instances{Style.RESET_ALL}{os.linesep}')
        print('{:<35}{:<23}{:<15}{:<15}{:<27}{:<10}'.format('Name', 'Instance ID', 'Private IP', 'Type', 'Launch Time',
                                                            'State'))
        print('{:<35}{:<23}{:<15}{:<15}{:<27}{:<10}'.format('----', '-----------', '----------', '----', '-----------',
                                                            '-----'))

        for instance in instances:
            print(
                '{:<35}{:<23}{:<15}{:<15}{:<27}{:<10}'.format(instance['name'], instance['id'], instance['private_ip'],
                                                              instance['type'],
                                                              instance['launch'].astimezone(zone).isoformat(),
                                                              instance['state']))

        print(f'{os.linesep * 2}{Fore.GREEN}AutoScaling Groups{Style.RESET_ALL}{os.linesep}')
        print('{:<65}{:<5}{:<5}{:<10}{:<10}{:<10}'.format("Name", "Min", "Max", "Desired", "Instances", "Status"))
        print('{:<65}{:<5}{:<5}{:<10}{:<10}{:<10}'.format("----", "---", "---", "-------", "---------", "------"))

        for asg in asgs:
            print('{:<65}{:<5}{:<5}{:<10}{:<10}{:<10}'.format(asg['name'], asg['min'], asg['max'], asg['desired'], '',
                                                              ''))


if __name__ == '__main__':
    cli(obj={})
