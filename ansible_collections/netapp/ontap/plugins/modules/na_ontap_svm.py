#!/usr/bin/python

# (c) 2018-2019, NetApp, Inc
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}


DOCUMENTATION = '''

module: na_ontap_svm

short_description: NetApp ONTAP SVM
extends_documentation_fragment:
    - netapp.ontap.netapp.na_ontap
version_added: '2.6'
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>

description:
- Create, modify or delete SVM on NetApp ONTAP

options:

  state:
    description:
    - Whether the specified SVM should exist or not.
    choices: ['present', 'absent']
    default: 'present'

  name:
    description:
    - The name of the SVM to manage.
    required: true

  from_name:
    description:
    - Name of the SVM to be renamed
    version_added: '2.7'

  root_volume:
    description:
    - Root volume of the SVM.
    - Cannot be modified after creation.

  root_volume_aggregate:
    description:
    - The aggregate on which the root volume will be created.
    - Cannot be modified after creation.

  root_volume_security_style:
    description:
    -   Security Style of the root volume.
    -   When specified as part of the vserver-create,
        this field represents the security style for the Vserver root volume.
    -   When specified as part of vserver-get-iter call,
        this will return the list of matching Vservers.
    -   The 'unified' security style, which applies only to Infinite Volumes,
        cannot be applied to a Vserver's root volume.
    -   Cannot be modified after creation.
    choices: ['unix', 'ntfs', 'mixed', 'unified']

  allowed_protocols:
    description:
    - Allowed Protocols.
    - When specified as part of a vserver-create,
      this field represent the list of protocols allowed on the Vserver.
    - When part of vserver-get-iter call,
      this will return the list of Vservers
      which have any of the protocols specified
      as part of the allowed-protocols.
    - When part of vserver-modify,
      this field should include the existing list
      along with new protocol list to be added to prevent data disruptions.
    - Possible values
    - nfs   NFS protocol,
    - cifs   CIFS protocol,
    - fcp   FCP protocol,
    - iscsi   iSCSI protocol,
    - ndmp   NDMP protocol,
    - http   HTTP protocol,
    - nvme   NVMe protocol

  aggr_list:
    description:
    - List of aggregates assigned for volume operations.
    - These aggregates could be shared for use with other Vservers.
    - When specified as part of a vserver-create,
      this field represents the list of aggregates
      that are assigned to the Vserver for volume operations.
    - When part of vserver-get-iter call,
      this will return the list of Vservers
      which have any of the aggregates specified as part of the aggr list.

  ipspace:
    description:
    - IPSpace name
    - Cannot be modified after creation.
    version_added: '2.7'


  snapshot_policy:
    description:
    - Default snapshot policy setting for all volumes of the Vserver.
      This policy will be assigned to all volumes created in this
      Vserver unless the volume create request explicitly provides a
      snapshot policy or volume is modified later with a specific
      snapshot policy. A volume-level snapshot policy always overrides
      the default Vserver-wide snapshot policy.
    version_added: '2.7'

  language:
    description:
    - Language to use for the SVM
    - Default to C.UTF-8
    - Possible values   Language
    - c                 POSIX
    - ar                Arabic
    - cs                Czech
    - da                Danish
    - de                German
    - en                English
    - en_us             English (US)
    - es                Spanish
    - fi                Finnish
    - fr                French
    - he                Hebrew
    - hr                Croatian
    - hu                Hungarian
    - it                Italian
    - ja                Japanese euc-j
    - ja_v1             Japanese euc-j
    - ja_jp.pck         Japanese PCK (sjis)
    - ja_jp.932         Japanese cp932
    - ja_jp.pck_v2      Japanese PCK (sjis)
    - ko                Korean
    - no                Norwegian
    - nl                Dutch
    - pl                Polish
    - pt                Portuguese
    - ro                Romanian
    - ru                Russian
    - sk                Slovak
    - sl                Slovenian
    - sv                Swedish
    - tr                Turkish
    - zh                Simplified Chinese
    - zh.gbk            Simplified Chinese (GBK)
    - zh_tw             Traditional Chinese euc-tw
    - zh_tw.big5        Traditional Chinese Big 5
    version_added: '2.7'

  subtype:
    description:
    - The subtype for vserver to be created.
    - Cannot be modified after creation.
    choices: ['default', 'dp_destination', 'sync_source', 'sync_destination']
    version_added: '2.7'

  comment:
    description:
    - When specified as part of a vserver-create, this field represents the comment associated with the Vserver.
    - When part of vserver-get-iter call, this will return the list of matching Vservers.
    version_added: '2.8'
'''

EXAMPLES = """

    - name: Create SVM
      na_ontap_svm:
        state: present
        name: ansibleVServer
        root_volume: vol1
        root_volume_aggregate: aggr1
        root_volume_security_style: mixed
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"

"""

RETURN = """
"""
import copy
import traceback

import ansible_collections.netapp.ontap.plugins.module_utils.netapp as netapp_utils
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
from ansible_collections.netapp.ontap.plugins.module_utils.netapp_module import NetAppModule
from ansible_collections.netapp.ontap.plugins.module_utils.netapp import OntapRestAPI

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppOntapSVM(object):

    def __init__(self):
        self.use_rest = False
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=[
                       'present', 'absent'], default='present'),
            name=dict(required=True, type='str'),
            from_name=dict(required=False, type='str'),
            root_volume=dict(type='str'),
            root_volume_aggregate=dict(type='str'),
            root_volume_security_style=dict(type='str', choices=['unix',
                                                                 'ntfs',
                                                                 'mixed',
                                                                 'unified'
                                                                 ]),
            allowed_protocols=dict(type='list'),
            aggr_list=dict(type='list'),
            ipspace=dict(type='str', required=False),
            snapshot_policy=dict(type='str', required=False),
            language=dict(type='str', required=False),
            subtype=dict(choices=['default', 'dp_destination', 'sync_source', 'sync_destination']),
            comment=dict(type="str", required=False)
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )
        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)

        self.restApi = OntapRestAPI(self.module)
        # with REST, to force synchronous operations
        self.timeout = self.restApi.timeout
        # root volume not supported with rest api
        unsupported_rest_properties = ['root_volume', 'root_volume_aggregate', 'root_volume_security_style']
        used_unsupported_rest_properties = [x for x in unsupported_rest_properties if x in self.parameters]
        self.use_rest, error = self.restApi.is_rest(used_unsupported_rest_properties)
        if error is not None:
            self.module.fail_json(msg=error)
        if not self.use_rest:
            if HAS_NETAPP_LIB is False:
                self.module.fail_json(
                    msg="the python NetApp-Lib module is required")
            else:
                self.server = netapp_utils.setup_na_ontap_zapi(module=self.module)

    @staticmethod
    def clean_up_output(vserver_details):
        vserver_details['root_volume'] = None
        vserver_details['root_volume_aggregate'] = None
        vserver_details['root_volume_security_style'] = None
        vserver_details['aggr_list'] = []
        for aggr in vserver_details['aggregates']:
            vserver_details['aggr_list'].append(aggr['name'])
        vserver_details.pop('aggregates')
        vserver_details['ipspace'] = vserver_details['ipspace']['name']
        vserver_details['snapshot_policy'] = vserver_details['snapshot_policy']['name']
        vserver_details['allowed_protocols'] = []
        if 'cifs' in vserver_details:
            if vserver_details['cifs']['enabled']:
                vserver_details['allowed_protocols'].append('cifs')
            vserver_details.pop('cifs')
        if 'fcp' in vserver_details:
            if vserver_details['fcp']['enabled']:
                vserver_details['allowed_protocols'].append('fcp')
            vserver_details.pop('fcp')
        if 'issi' in vserver_details:
            if vserver_details['iscsi']['enabled']:
                vserver_details['allowed_protocols'].append('iscsi')
            vserver_details.pop('iscsi')
        if 'nvme' in vserver_details:
            if vserver_details['nvme']['enabled']:
                vserver_details['allowed_protocols'].append('nvme')
            vserver_details.pop('nvme')
        if 'nfs' in vserver_details:
            if vserver_details['nfs']['enabled']:
                vserver_details['allowed_protocols'].append('nfs')
            vserver_details.pop('nfs')
        return vserver_details

    def get_vserver(self, vserver_name=None):
        """
        Checks if vserver exists.

        :return:
            vserver object if vserver found
            None if vserver is not found
        :rtype: object/None
        """
        if vserver_name is None:
            vserver_name = self.parameters['name']

        if self.use_rest:
            api = 'svm/svms'
            params = {'fields': 'subtype,aggregates,language,snapshot_policy,ipspace,comment,nfs,cifs,fcp,iscsi,nvme'}
            message, error = self.restApi.get(api, params)
            if error:
                self.module.fail_json(msg=error)
            if len(message.keys()) == 0:
                return None
            elif 'records' in message and len(message['records']) == 0:
                return None
            elif 'records' not in message:
                error = "Unexpected response in get_net_route from %s: %s" % (api, repr(message))
                self.module.fail_json(msg=error)
            vserver_details = None
            for record in message['records']:
                if record['name'] == vserver_name:
                    vserver_details = copy.deepcopy(record)
                    break
            if vserver_details is None:
                return None
            return self.clean_up_output(vserver_details)

        else:
            vserver_info = netapp_utils.zapi.NaElement('vserver-get-iter')
            query_details = netapp_utils.zapi.NaElement.create_node_with_children(
                'vserver-info', **{'vserver-name': vserver_name})

            query = netapp_utils.zapi.NaElement('query')
            query.add_child_elem(query_details)
            vserver_info.add_child_elem(query)

            result = self.server.invoke_successfully(vserver_info,
                                                     enable_tunneling=False)
            vserver_details = None
            if (result.get_child_by_name('num-records') and
                    int(result.get_child_content('num-records')) >= 1):
                attributes_list = result.get_child_by_name('attributes-list')
                vserver_info = attributes_list.get_child_by_name('vserver-info')
                aggr_list = list()
                ''' vserver aggr-list can be empty by default'''
                get_list = vserver_info.get_child_by_name('aggr-list')
                if get_list is not None:
                    aggregates = get_list.get_children()
                    for aggr in aggregates:
                        aggr_list.append(aggr.get_content())

                protocols = list()
                '''allowed-protocols is not empty for data SVM, but is for node SVM'''
                allowed_protocols = vserver_info.get_child_by_name('allowed-protocols')
                if allowed_protocols is not None:
                    get_protocols = allowed_protocols.get_children()
                    for protocol in get_protocols:
                        protocols.append(protocol.get_content())
                vserver_details = {'name': vserver_info.get_child_content('vserver-name'),
                                   'root_volume': vserver_info.get_child_content('root-volume'),
                                   'root_volume_aggregate': vserver_info.get_child_content('root-volume-aggregate'),
                                   'root_volume_security_style': vserver_info.get_child_content('root-volume-security-style'),
                                   'subtype': vserver_info.get_child_content('vserver-subtype'),
                                   'aggr_list': aggr_list,
                                   'language': vserver_info.get_child_content('language'),
                                   'snapshot_policy': vserver_info.get_child_content('snapshot-policy'),
                                   'allowed_protocols': protocols,
                                   'ipspace': vserver_info.get_child_content('ipspace'),
                                   'comment': vserver_info.get_child_content('comment')}
            return vserver_details

    def create_vserver(self):
        if self.use_rest:
            api = 'svm/svms'
            params = {'name': self.parameters['name']}
            if self.parameters.get('language'):
                params['language'] = self.parameters['language']
            if self.parameters.get('ipspace'):
                params['ipspace'] = self.parameters['ipspace']
            if self.parameters.get('snapshot_policy'):
                params['snapshot_policy'] = self.parameters['snapshot_policy']
            if self.parameters.get('subtype'):
                params['subtype'] = self.parameters['subtype']
            if self.parameters.get('comment'):
                params['comment'] = self.parameters['comment']
            if self.parameters.get('aggr_list'):
                params['aggregates'] = []
                for aggr in self.parameters['aggr_list']:
                    params['aggregates'].append({'name': aggr})
            if self.parameters.get('allowed_protocols'):
                for protocol in self.parameters['allowed_protocols']:
                    params[protocol] = {'enabled': 'true'}
            # for a sync operation
            data = {'return_timeout': self.timeout}
            __, error = self.restApi.post(api, params, data)
            if error:
                self.module.fail_json(msg=error)
        else:
            options = {'vserver-name': self.parameters['name']}
            self.add_parameter_to_dict(options, 'root_volume', 'root-volume')
            self.add_parameter_to_dict(options, 'root_volume_aggregate', 'root-volume-aggregate')
            self.add_parameter_to_dict(options, 'root_volume_security_style', 'root-volume-security-style')
            self.add_parameter_to_dict(options, 'language', 'language')
            self.add_parameter_to_dict(options, 'ipspace', 'ipspace')
            self.add_parameter_to_dict(options, 'snapshot_policy', 'snapshot-policy')
            self.add_parameter_to_dict(options, 'subtype', 'vserver-subtype')
            self.add_parameter_to_dict(options, 'comment', 'comment')
            vserver_create = netapp_utils.zapi.NaElement.create_node_with_children('vserver-create', **options)
            try:
                self.server.invoke_successfully(vserver_create,
                                                enable_tunneling=False)
            except netapp_utils.zapi.NaApiError as e:
                self.module.fail_json(msg='Error provisioning SVM %s: %s'
                                          % (self.parameters['name'], to_native(e)),
                                      exception=traceback.format_exc())
            # add allowed-protocols, aggr-list after creation,
            # since vserver-create doesn't allow these attributes during creation
            options = dict()
            for key in ('allowed_protocols', 'aggr_list'):
                if self.parameters.get(key):
                    options[key] = self.parameters[key]
            if options:
                self.modify_vserver(options)

    def delete_vserver(self, current=None):
        if self.use_rest:
            if current is None:
                self.module.fail_json(msg='Internal error, expecting SVM object in delete')
            api = 'svm/svms/%s' % current['uuid']
            params = {}
            # for a sync operation
            data = {'return_timeout': self.timeout}
            __, error = self.restApi.delete(api, params, data)
            if error:
                self.module.fail_json(msg=error)
        else:
            vserver_delete = netapp_utils.zapi.NaElement.create_node_with_children(
                'vserver-destroy', **{'vserver-name': self.parameters['name']})

            try:
                self.server.invoke_successfully(vserver_delete,
                                                enable_tunneling=False)
            except netapp_utils.zapi.NaApiError as e:
                self.module.fail_json(msg='Error deleting SVM %s: %s'
                                          % (self.parameters['name'], to_native(e)),
                                      exception=traceback.format_exc())

    def rename_vserver(self, current=None):
        if self.use_rest:
            if current is None:
                self.module.fail_json(msg='Internal error, expecting SVM object in rename')
            api = 'svm/svms/%s' % current['uuid']
            params = {'name': self.parameters['name']}
            # for a sync operation
            data = {'return_timeout': self.timeout}
            __, error = self.restApi.patch(api, params, data)
            if error:
                self.module.fail_json(msg=error)
        else:
            vserver_rename = netapp_utils.zapi.NaElement.create_node_with_children(
                'vserver-rename', **{'vserver-name': self.parameters['from_name'],
                                     'new-name': self.parameters['name']})

            try:
                self.server.invoke_successfully(vserver_rename,
                                                enable_tunneling=False)
            except netapp_utils.zapi.NaApiError as e:
                self.module.fail_json(msg='Error renaming SVM %s: %s'
                                      % (self.parameters['from_name'], to_native(e)),
                                      exception=traceback.format_exc())

    def modify_vserver(self, modify, current=None):
        '''
        Modify vserver.
        :param modify: list of modify attributes
        :param current: with rest, SVM object to modify
        '''
        if self.use_rest:
            if current is None:
                self.module.fail_json(msg='Internal error, expecting SVM object in modify')
            api = 'svm/svms/%s' % current['uuid']
            for attribute in modify:
                if attribute == 'snapshot_policy' or attribute == 'allowed_protocols' or attribute == 'aggr_list':
                    self.module.fail_json(msg='REST API does not support modify of %s' % attribute)
            # for a sync operation
            data = {'return_timeout': self.timeout}
            __, error = self.restApi.patch(api, modify, data)
            if error:
                self.module.fail_json(msg=error)
        else:
            vserver_modify = netapp_utils.zapi.NaElement('vserver-modify')
            vserver_modify.add_new_child('vserver-name', self.parameters['name'])
            for attribute in modify:
                if attribute == 'language':
                    vserver_modify.add_new_child('language', self.parameters['language'])
                if attribute == 'snapshot_policy':
                    vserver_modify.add_new_child('snapshot_policy', self.parameters['snapshot_policy'])
                if attribute == 'comment':
                    vserver_modify.add_new_child('comment', self.parameters['comment'])
                if attribute == 'allowed_protocols':
                    allowed_protocols = netapp_utils.zapi.NaElement('allowed-protocols')
                    for protocol in self.parameters['allowed_protocols']:
                        allowed_protocols.add_new_child('protocol', protocol)
                    vserver_modify.add_child_elem(allowed_protocols)
                if attribute == 'aggr_list':
                    aggregates = netapp_utils.zapi.NaElement('aggr-list')
                    for aggr in self.parameters['aggr_list']:
                        aggregates.add_new_child('aggr-name', aggr)
                    vserver_modify.add_child_elem(aggregates)
            try:
                self.server.invoke_successfully(vserver_modify,
                                                enable_tunneling=False)
            except netapp_utils.zapi.NaApiError as e:
                self.module.fail_json(msg='Error modifying SVM %s: %s'
                                      % (self.parameters['name'], to_native(e)),
                                      exception=traceback.format_exc())

    def add_parameter_to_dict(self, adict, name, key=None, tostr=False):
        '''
        add defined parameter (not None) to adict using key.
        :param adict: a dictionary.
        :param name: name in self.parameters.
        :param key:  key in adict.
        :param tostr: boolean.
        '''
        if key is None:
            key = name
        if self.parameters.get(name) is not None:
            if tostr:
                adict[key] = str(self.parameters.get(name))
            else:
                adict[key] = self.parameters.get(name)

    def apply(self):
        '''Call create/modify/delete operations.'''
        if not self.use_rest:
            self.asup_log_for_cserver("na_ontap_svm")
        current = self.get_vserver()
        cd_action, rename = None, None
        if self.parameters.get('from_name'):
            old_svm = self.get_vserver(self.parameters['from_name'])
            rename = self.na_helper.is_rename_action(old_svm, current)
            if rename is None:
                self.module.fail_json(msg='Error renaming SVM %s: no SVM with from_name %s.' % (self.parameters['name'], self.parameters['from_name']))
        else:
            cd_action = self.na_helper.get_cd_action(current, self.parameters)
        modify = self.na_helper.get_modified_attributes(current, self.parameters)
        for attribute in modify:
            if attribute in ['root_volume', 'root_volume_aggregate', 'root_volume_security_style', 'subtype', 'ipspace']:
                self.module.fail_json(msg='Error modifying SVM %s: can not modify %s.' % (self.parameters['name'], attribute))
            if attribute == 'language':
                # Ontap documentation uses C.UTF-8, but actually stores as c.utf_8.
                if self.parameters['language'].lower() == 'c.utf-8':
                    self.parameters['language'] = 'c.utf_8'
        if self.na_helper.changed:
            if self.module.check_mode:
                pass
            else:
                if rename:
                    self.rename_vserver(old_svm)
                # If rename is True, cd_action is None, but modify could be true or false.
                if cd_action == 'create':
                    self.create_vserver()
                elif cd_action == 'delete':
                    self.delete_vserver(current)
                elif modify:
                    self.modify_vserver(modify, current)
        self.module.exit_json(changed=self.na_helper.changed)

    def asup_log_for_cserver(self, event_name):
        """
        Fetch admin vserver for the given cluster
        Create and Autosupport log event with the given module name
        :param event_name: Name of the event log
        :return: None
        """
        results = netapp_utils.get_cserver(self.server)
        cserver = netapp_utils.setup_na_ontap_zapi(module=self.module, vserver=results)
        netapp_utils.ems_log_event(event_name, cserver)


def main():
    '''Apply vserver operations from playbook'''
    v = NetAppOntapSVM()
    v.apply()


if __name__ == '__main__':
    main()
