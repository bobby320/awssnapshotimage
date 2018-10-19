import boto3
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

@click.group()
def cli():
    """Snapshot mantains snapshot of volumes"""

@cli.group('snapshot')
def snapshot():
    """Commands for Snapshot"""

@snapshot.command('list')
@click.option('--project', default=None, help="only volumes for project (tag Project:<name>)")
def list_snapshot(project):
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
def create_snapshot(project):
    "Creates snapshot for EC2 instances"
    instances = filter_instances(project)

    for i in instances:
        i.stop()
        for v in i.volumes.all():
            print("creating snapshot of {0}...".format(v.id))
            v.create.snapshot(Description="Created by snapshot.py script")
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
def stop_instances(project):
    "stop ec2 instances"
    instances = filter_instances(project)

    for i in instances:
        print("stopping {0}...".format(i.id))
        i.stop()
    return

@instances.command('start')
@click.option('--project', default=None, help="only instances for project (tag Project:<name>)")
def start_instances(project):
    "start ec2 instances"
    instances = filter_instances(project)

    for i in instances:
        print("starting {0}...".format(i.id))
        i.start()
    return

if __name__ == '__main__':
    cli()
