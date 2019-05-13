import os
import click

from aws import Aws
from colorama import Fore
from colorama import Style
from dateutil import tz
import time


@click.group()
@click.option('-p', '--product', envvar='PRODUCT', help='The product to operate on (defaults to $PRODUCT)')
@click.option('-e', '--env', envvar='ENV', help='The environment to operate on (defaults to $ENV)')
@click.option('-b', '--profile', envvar='AWS_PROFILE', help='The AWS profile to use (defaults to $AWS_PROFILE)')
@click.option('-r', '--region', envvar='AWS_REGION', help='The AWS region to use (defaults to $AWS_REGION)')
@click.option('-f', '--format', default='text', envvar='ENVMANAGE_FORMAT', help='The format to output in',
              type=click.Choice(['text', 'json']))
@click.pass_context
def cli(ctx, product, env, profile, region, format):
    aws = Aws(region, profile, product, env, format)
    ctx.obj['AWS'] = aws
    ctx.obj['FORMAT'] = format


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
    if ctx.obj['FORMAT'] == 'json':
        print(secret)
    else:
        print(f"{Fore.GREEN}{secret['name']}{Style.RESET_ALL} ({Fore.LIGHTBLUE_EX}{secret['type']}{Style.RESET_ALL}) "
              + f"= {Fore.LIGHTRED_EX}{secret['value']}{Style.RESET_ALL}")


@cli.command(help="Set a secret's value")
@click.option('-n', '--name', help='The name of the secret to set', required=True)
@click.option('-v', '--value', help='The value to set the secret to', required=True)
@click.option('--encrypt', is_flag=True, help='Whether to create an encrypted secret', default=True)
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
    aws = ctx.obj['AWS']
    aws.show_k8s_dashboard()


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
