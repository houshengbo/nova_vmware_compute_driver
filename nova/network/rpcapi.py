# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012, Red Hat, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Client side of the network RPC API.
"""

from nova.openstack.common import cfg
from nova.openstack.common import jsonutils
from nova.openstack.common import rpc
from nova.openstack.common.rpc import proxy as rpc_proxy

CONF = cfg.CONF
CONF.import_opt('network_topic', 'nova.config')


class NetworkAPI(rpc_proxy.RpcProxy):
    '''Client side of the network rpc API.

    API version history:

        1.0 - Initial version.
        1.1 - Adds migrate_instance_[start|finish]
        1.2 - Make migrate_instance_[start|finish] a little more flexible
        1.3 - Adds fanout cast update_dns for multi_host networks
        1.4 - Add get_backdoor_port()
        1.5 - Adds associate
        1.6 - Adds instance_uuid to _{dis,}associate_floating_ip
    '''

    #
    # NOTE(russellb): This is the default minimum version that the server
    # (manager) side must implement unless otherwise specified using a version
    # argument to self.call()/cast()/etc. here.  It should be left as X.0 where
    # X is the current major API version (1.0, 2.0, ...).  For more information
    # about rpc API versioning, see the docs in
    # openstack/common/rpc/dispatcher.py.
    #
    BASE_RPC_API_VERSION = '1.0'

    def __init__(self, topic=None):
        topic = topic if topic else CONF.network_topic
        super(NetworkAPI, self).__init__(
                topic=topic,
                default_version=self.BASE_RPC_API_VERSION)

    def get_all_networks(self, ctxt):
        return self.call(ctxt, self.make_msg('get_all_networks'))

    def get_network(self, ctxt, network_uuid):
        return self.call(ctxt, self.make_msg('get_network',
                network_uuid=network_uuid))

    # TODO(russellb): Convert this to named arguments.  It's a pretty large
    # list, so unwinding it all is probably best done in its own patch so it's
    # easier to review.
    def create_networks(self, ctxt, **kwargs):
        return self.call(ctxt, self.make_msg('create_networks', **kwargs))

    def delete_network(self, ctxt, uuid, fixed_range):
        return self.call(ctxt, self.make_msg('delete_network',
                uuid=uuid, fixed_range=fixed_range))

    def disassociate_network(self, ctxt, network_uuid):
        return self.call(ctxt, self.make_msg('disassociate_network',
                network_uuid=network_uuid))

    def get_fixed_ip(self, ctxt, id):
        return self.call(ctxt, self.make_msg('get_fixed_ip', id=id))

    def get_fixed_ip_by_address(self, ctxt, address):
        return self.call(ctxt, self.make_msg('get_fixed_ip_by_address',
                address=address))

    def get_floating_ip(self, ctxt, id):
        return self.call(ctxt, self.make_msg('get_floating_ip', id=id))

    def get_floating_pools(self, ctxt):
        return self.call(ctxt, self.make_msg('get_floating_pools'))

    def get_floating_ip_by_address(self, ctxt, address):
        return self.call(ctxt, self.make_msg('get_floating_ip_by_address',
                address=address))

    def get_floating_ips_by_project(self, ctxt):
        return self.call(ctxt, self.make_msg('get_floating_ips_by_project'))

    def get_floating_ips_by_fixed_address(self, ctxt, fixed_address):
        return self.call(ctxt, self.make_msg(
                'get_floating_ips_by_fixed_address',
                fixed_address=fixed_address))

    def get_instance_id_by_floating_address(self, ctxt, address):
        return self.call(ctxt, self.make_msg(
                'get_instance_id_by_floating_address',
                address=address))

    def get_backdoor_port(self, ctxt, host):
        return self.call(ctxt, self.make_msg('get_backdoor_port'),
                         topic=rpc.queue_get_for(ctxt, self.topic, host),
                         version='1.4')

    def get_vifs_by_instance(self, ctxt, instance_id):
        # NOTE(vish): When the db calls are converted to store network
        #             data by instance_uuid, this should pass uuid instead.
        return self.call(ctxt, self.make_msg('get_vifs_by_instance',
                instance_id=instance_id))

    def get_vif_by_mac_address(self, ctxt, mac_address):
        return self.call(ctxt, self.make_msg('get_vif_by_mac_address',
                mac_address=mac_address))

    def allocate_floating_ip(self, ctxt, project_id, pool, auto_assigned):
        return self.call(ctxt, self.make_msg('allocate_floating_ip',
                project_id=project_id, pool=pool, auto_assigned=auto_assigned))

    def deallocate_floating_ip(self, ctxt, address, affect_auto_assigned):
        return self.call(ctxt, self.make_msg('deallocate_floating_ip',
            address=address, affect_auto_assigned=affect_auto_assigned))

    def associate_floating_ip(self, ctxt, floating_address, fixed_address,
                              affect_auto_assigned):
        return self.call(ctxt, self.make_msg('associate_floating_ip',
                floating_address=floating_address, fixed_address=fixed_address,
                affect_auto_assigned=affect_auto_assigned))

    def disassociate_floating_ip(self, ctxt, address, affect_auto_assigned):
        return self.call(ctxt, self.make_msg('disassociate_floating_ip',
                address=address, affect_auto_assigned=affect_auto_assigned))

    def allocate_for_instance(self, ctxt, instance_id, instance_uuid,
                              project_id, host, rxtx_factor, vpn,
                              requested_networks):
        return self.call(ctxt, self.make_msg('allocate_for_instance',
                instance_id=instance_id, instance_uuid=instance_uuid,
                project_id=project_id, host=host, rxtx_factor=rxtx_factor,
                vpn=vpn, requested_networks=requested_networks))

    def deallocate_for_instance(self, ctxt, instance_id, project_id, host):
        return self.call(ctxt, self.make_msg('deallocate_for_instance',
                instance_id=instance_id, project_id=project_id, host=host))

    def add_fixed_ip_to_instance(self, ctxt, instance_id, host, network_id):
        return self.call(ctxt, self.make_msg('add_fixed_ip_to_instance',
                instance_id=instance_id, host=host, network_id=network_id))

    def remove_fixed_ip_from_instance(self, ctxt, instance_id, host, address):
        return self.call(ctxt, self.make_msg('remove_fixed_ip_from_instance',
                instance_id=instance_id, host=host, address=address))

    def add_network_to_project(self, ctxt, project_id, network_uuid):
        return self.call(ctxt, self.make_msg('add_network_to_project',
                project_id=project_id, network_uuid=network_uuid))

    def associate(self, ctxt, network_uuid, associations):
        return self.call(ctxt, self.make_msg('associate',
                network_uuid=network_uuid, associations=associations),
                self.topic, version="1.5")

    def get_instance_nw_info(self, ctxt, instance_id, instance_uuid,
                             rxtx_factor, host, project_id):
        return self.call(ctxt, self.make_msg('get_instance_nw_info',
                instance_id=instance_id, instance_uuid=instance_uuid,
                rxtx_factor=rxtx_factor, host=host, project_id=project_id))

    def validate_networks(self, ctxt, networks):
        return self.call(ctxt, self.make_msg('validate_networks',
                networks=networks))

    def get_instance_uuids_by_ip_filter(self, ctxt, filters):
        return self.call(ctxt, self.make_msg('get_instance_uuids_by_ip_filter',
                filters=filters))

    def get_dns_domains(self, ctxt):
        return self.call(ctxt, self.make_msg('get_dns_domains'))

    def add_dns_entry(self, ctxt, address, name, dns_type, domain):
        return self.call(ctxt, self.make_msg('add_dns_entry', address=address,
                name=name, dns_type=dns_type, domain=domain))

    def modify_dns_entry(self, ctxt, address, name, domain):
        return self.call(ctxt, self.make_msg('modify_dns_entry',
                address=address, name=name, domain=domain))

    def delete_dns_entry(self, ctxt, name, domain):
        return self.call(ctxt, self.make_msg('delete_dns_entry',
                name=name, domain=domain))

    def delete_dns_domain(self, ctxt, domain):
        return self.call(ctxt, self.make_msg('delete_dns_domain',
                domain=domain))

    def get_dns_entries_by_address(self, ctxt, address, domain):
        return self.call(ctxt, self.make_msg('get_dns_entries_by_address',
                address=address, domain=domain))

    def get_dns_entries_by_name(self, ctxt, name, domain):
        return self.call(ctxt, self.make_msg('get_dns_entries_by_name',
                name=name, domain=domain))

    def create_private_dns_domain(self, ctxt, domain, av_zone):
        return self.call(ctxt, self.make_msg('create_private_dns_domain',
                domain=domain, av_zone=av_zone))

    def create_public_dns_domain(self, ctxt, domain, project):
        return self.call(ctxt, self.make_msg('create_public_dns_domain',
                domain=domain, project=project))

    def setup_networks_on_host(self, ctxt, instance_id, host, teardown):
        # NOTE(tr3buchet): the call is just to wait for completion
        return self.call(ctxt, self.make_msg('setup_networks_on_host',
                instance_id=instance_id, host=host, teardown=teardown))

    def set_network_host(self, ctxt, network_ref):
        network_ref_p = jsonutils.to_primitive(network_ref)
        return self.call(ctxt, self.make_msg('set_network_host',
                network_ref=network_ref_p))

    def rpc_setup_network_on_host(self, ctxt, network_id, teardown, host):
        # NOTE(tr3buchet): the call is just to wait for completion
        return self.call(ctxt, self.make_msg('rpc_setup_network_on_host',
                network_id=network_id, teardown=teardown),
                topic=rpc.queue_get_for(ctxt, self.topic, host))

    # NOTE(russellb): Ideally this would not have a prefix of '_' since it is
    # a part of the rpc API. However, this is how it was being called when the
    # 1.0 API was being documented using this client proxy class.  It should be
    # changed if there was ever a 2.0.
    def _rpc_allocate_fixed_ip(self, ctxt, instance_id, network_id, address,
                               vpn, host):
        return self.call(ctxt, self.make_msg('_rpc_allocate_fixed_ip',
                instance_id=instance_id, network_id=network_id,
                address=address, vpn=vpn),
                topic=rpc.queue_get_for(ctxt, self.topic, host))

    def deallocate_fixed_ip(self, ctxt, address, host):
        return self.call(ctxt, self.make_msg('deallocate_fixed_ip',
                address=address, host=host),
                topic=rpc.queue_get_for(ctxt, self.topic, host))

    def update_dns(self, ctxt, network_ids):
        return self.fanout_cast(ctxt, self.make_msg('update_dns',
                network_ids=network_ids), version='1.3')

    # NOTE(russellb): Ideally this would not have a prefix of '_' since it is
    # a part of the rpc API. However, this is how it was being called when the
    # 1.0 API was being documented using this client proxy class.  It should be
    # changed if there was ever a 2.0.
    def _associate_floating_ip(self, ctxt, floating_address, fixed_address,
                               interface, host, instance_uuid=None):
        return self.call(ctxt, self.make_msg('_associate_floating_ip',
                floating_address=floating_address, fixed_address=fixed_address,
                interface=interface, instance_uuid=instance_uuid),
                topic=rpc.queue_get_for(ctxt, self.topic, host),
                version='1.6')

    # NOTE(russellb): Ideally this would not have a prefix of '_' since it is
    # a part of the rpc API. However, this is how it was being called when the
    # 1.0 API was being documented using this client proxy class.  It should be
    # changed if there was ever a 2.0.
    def _disassociate_floating_ip(self, ctxt, address, interface, host,
                                  instance_uuid=None):
        return self.call(ctxt, self.make_msg('_disassociate_floating_ip',
                address=address, interface=interface,
                instance_uuid=instance_uuid),
                topic=rpc.queue_get_for(ctxt, self.topic, host),
                version='1.6')

    def lease_fixed_ip(self, ctxt, address, host):
        self.cast(ctxt, self.make_msg('lease_fixed_ip', address=address),
                  topic=rpc.queue_get_for(ctxt, self.topic, host))

    def release_fixed_ip(self, ctxt, address, host):
        self.cast(ctxt, self.make_msg('release_fixed_ip', address=address),
                  topic=rpc.queue_get_for(ctxt, self.topic, host))

    def migrate_instance_start(self, ctxt, instance_uuid, rxtx_factor,
                               project_id, source_compute, dest_compute,
                               floating_addresses, host=None):
        topic = rpc.queue_get_for(ctxt, self.topic, host)
        return self.call(ctxt, self.make_msg(
                'migrate_instance_start',
                instance_uuid=instance_uuid,
                rxtx_factor=rxtx_factor,
                project_id=project_id,
                source=source_compute,
                dest=dest_compute,
                floating_addresses=floating_addresses),
                topic=topic,
                version='1.2')

    def migrate_instance_finish(self, ctxt, instance_uuid, rxtx_factor,
                                project_id, source_compute, dest_compute,
                                floating_addresses, host=None):
        topic = rpc.queue_get_for(ctxt, self.topic, host)
        return self.call(ctxt, self.make_msg(
                'migrate_instance_finish',
                instance_uuid=instance_uuid,
                rxtx_factor=rxtx_factor,
                project_id=project_id,
                source=source_compute,
                dest=dest_compute,
                floating_addresses=floating_addresses),
                topic=topic,
                version='1.2')
