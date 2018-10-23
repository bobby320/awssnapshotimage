import boto3
import botocore
import click

session = boto3.Session(profile_name='snapshot')
ec2 = session.resource('ec2')

def filter_instances(project):
    instances = []

    if project:
        filters = [{'Name':'tag:Project', 'Values':[project]}]
        instances = ec2.instances.filter(Filters=filters)
    else:
        instances = ec2.instances.all()

    return instances

def has_pending_snaphost(volume):
    snapshots = list(volume.snapshots.all())
    return snapshots and snapshot[0].state == 'pending'

@click.group()
def cli():
    """Snapshot mantains snapshot of volumes"""

@cli.group('snapshot')
def snapshot():
    """Commands for Snapshot"""

@snapshot.command('list')
@click.option('--project', default=None,
    help="only volumes for project (tag Project:<name>)")
@click.option('--all', 'list_all', default=False, is_flag=True,
    help="list all snapshots for each volume, not just recent")
def list_snapshot(project, list_all):
    "List ec2 snapshot"
    instances = filter_instances(project)
    for i in instances:
        for v in i.volumes.all():
            for s in v.snapshots.all():
                print(', '.join((
                s.id,
                v.id,
                i.id,
                s.state,
                s.progress,
                s.start_time.strftime("%c")
                )))

                if s.state == 'completed' and not list_all: break
    return

@cli.group('volumes')
def volumes():
    """Commands for Volumes"""

@volumes.command('list')
@click.option('--project', default=None, help="only volumes for project (tag Project:<name>)")
def list_volumes(project):
    "List ec2 volumes"
    instances = filter_instances(project)
    for i in instances:
        for v in i.volumes.all():
            print(', '.join((
            v.id,
            i.id,
            v.state,
            str(v.size) + "GB",
            v.encrypted and "Encrypted" or "Not Encrypted"
            )))
    return

@cli.group()
def instances():
    """Commands for Instances"""

@instances.command('snapshot')
@click.option('--project', default=None, help="only instances for project (tag Project:<name>)")
@click.option('--force', 'force_all', default=False, is_flag=True,
    help="Force option to take snapshot of all instances, if project not specified")
def create_snapshot(project, force_all):
    "Creates snapshot for EC2 instances"

    instances = filter_instances(project)

    if project is not None or force_all:
        for i in instances:

            print("stopping {0}..".format(i.id))
            i.stop()
            i.wait_until_stopped()

            for v in i.volumes.all():
                if has_pending_snaphost(v):
                    print("snapshot {0}, snapshot already in progress".format(v.id))
                    continue
                print("creating snapshot of {0}...".format(v.id))
                v.create_snapshot(Description="Created by snapshot.py script")

            print("starting {0}..".format(i.id))
            i.start()
            i.wait_until_running()
    else:
        print("Warning : Specify Project name or use --force to create snapshots")

    print("job done!!")
    return

@instances.command('list')
@click.option('--project', default=None, help="only instances for project (tag Project:<name>)")
def list_instances(project):
    "List ec2 instances"
    instances = filter_instances(project)

    for i in instances:
        tags = { t['Key']: t['Value'] for t in i.tags or []}
        print(', '.join((
            i.id,
            i.instance_type,
            i.placement['AvailabilityZone'],
            i.state['Name'],
            i.public_dns_name,
            tags.get('Project', '<no project>'))))
    return

@instances.command('stop')
@click.option('--project', default=None, help="only instances for project (tag Project:<name>)")
@click.option('--force', 'force_all', default=False, is_flag=True,
    help="Force option will stop all instances, if project not specified")
def stop_instances(project, force_all):
    "stop ec2 instances"

    instances = filter_instances(project)

    if project is not None or force_all:
        for i in instances:
            print("stopping {0}...".format(i.id))
            try:
                i.stop()
            except botocore.exceptions.ClientError as e:
                print("Count not stop {0}. ".format(i.id) + str(e))
                continue
    else:
        print("Warning : Specify Project name or use --force to stop the instances")
    return

@instances.command('start')
@click.option('--project', default=None, help="only instances for project (tag Project:<name>)")
@click.option('--force', 'force_all', default=False, is_flag=True,
    help="Force option will start all instances, if project not specified")
def start_instances(project, force_all):
    "start ec2 instances"

    instances = filter_instances(project)
    if project is not None or force_all:
        for i in instances:
            print("starting {0}...".format(i.id))
            try:
                i.start()
            except botocore.exceptions.ClientError as e:
                print("Count not start {0}. ".format(i.id) + str(e))
                continue
    else:
        print("Warning : Specify Project name or use --force to start the instances")
    return

@instances.command('reboot')
@click.option('--project', default=None, help="only instances for project (tag Project:<name>)")
@click.option('--force', 'force_all', default=False, is_flag=True,
    help="Force option will reboot all instances, if project not specified")
def restart_instances(project, force_all):
    "rebooting ec2 instances"

    instances = filter_instances(project)

    if project is not None or force_all:
        for i in instances:
            print("rebooting {0}...".format(i.id))
            try:
                i.reboot()
            except botocore.exceptions.ClientError as e:
                print("Count not start {0}. ".format(i.id) + str(e))
                continue
    else:
        print("Warning : Specify Project name or use --force to reboot the instances")
    return

if __name__ == '__main__':
    cli()
