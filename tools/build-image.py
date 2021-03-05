from time import sleep
import googleapiclient.discovery

import config as conf
import utils

compute = googleapiclient.discovery.build('compute', 'v1')
instance = None
instance_ip = None

### Create EC2 instance to setup MeiliSearch

print('Creating GCP Compute instance')

source_image = compute.images().getFromFamily(
    project='ubuntu-os-cloud',
    family=conf.DEBIAN_BASE_IMAGE_FAMILY
).execute()['selfLink']

# DOCS: https://cloud.google.com/compute/docs/reference/rest/v1/instances/insert
config = {
    'name': conf.INSTANCE_BUILD_NAME,
    'machineType': conf.INSTANCE_TYPE,
    'disks': [
        {
            'boot': True,
            'autoDelete': True,
            'initializeParams': {
                'sourceImage': source_image,
            }
        }
    ],
    "tags": {
        "items": [
            "http-server",
            "https-server"
        ],
    },

    # Specify a network interface with NAT to access the public
    # internet.
    'networkInterfaces': [{
        'network': 'global/networks/default',
        'accessConfigs': [
            {'type': 'ONE_TO_ONE_NAT', 'name': 'External NAT'}
        ]
    }],

    #user-data
    'metadata': {
        'items': [
            {
                'key': 'user-data',
                'value': conf.USER_DATA,
            }
        ]
    }
}
create = compute.instances().insert(
        project=conf.GCP_DEFAULT_PROJECT,
        zone=conf.GCP_DEFAULT_ZONE,
        body=config).execute()
print('   Instance created. ID: {}'.format(create['name']))


### Wait for EC2 instance to be 'RUNNING'

print('Waiting for GCP Compute instance state to be "RUNNING"')
state_code, state = utils.wait_for_instance_running(instance, conf.GCP_DEFAULT_PROJECT, conf.GCP_DEFAULT_ZONE, timeout_seconds=600)
print('   Instance state: {}'.format(state))

if state_code == utils.STATUS_OK:
    instance = compute.instances().get(project = conf.GCP_DEFAULT_PROJECT, zone=conf.GCP_DEFAULT_ZONE, instance=conf.INSTANCE_BUILD_NAME).execute()
    instance_ip = instance['networkInterfaces'][0]['accessConfigs'][0]['natIP']
    print('   Instance IP: {}'.format(instance_ip))
else:
    print('   Error: {}. State: {}.'.format(state_code, state))
    utils.terminate_instance_and_exit(instance)
