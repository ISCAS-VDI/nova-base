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

import datetime

from oslo_serialization import jsonutils
from oslo_utils import uuidutils

from nova import context
from nova import objects
from nova.objects import fields
from nova.tests.unit import fake_instance


def fake_db_req(**updates):
    ctxt = context.RequestContext('fake-user', 'fake-project')
    instance_uuid = uuidutils.generate_uuid()
    instance = fake_instance.fake_instance_obj(ctxt, objects.Instance,
            uuid=instance_uuid)
    db_build_request = {
            'id': 1,
            'project_id': 'fake-project',
            'instance_uuid': instance_uuid,
            'instance': jsonutils.dumps(instance.obj_to_primitive()),
            'created_at': datetime.datetime(2016, 1, 16),
            'updated_at': datetime.datetime(2016, 1, 16),
    }

    for name, field in objects.BuildRequest.fields.items():
        if name in db_build_request:
            continue
        if field.nullable:
            db_build_request[name] = None
        elif field.default != fields.UnspecifiedDefault:
            db_build_request[name] = field.default
        else:
            raise Exception('fake_db_req needs help with %s' % name)

    if updates:
        db_build_request.update(updates)

    return db_build_request


def fake_req_obj(ctxt, db_req=None):
    if db_req is None:
        db_req = fake_db_req()
    req_obj = objects.BuildRequest(ctxt)
    for field in req_obj.fields:
        value = db_req[field]
        # create() can't be called if this is set
        if field == 'id':
            continue
        if isinstance(req_obj.fields[field], fields.ObjectField):
            value = value
            if field == 'instance':
                req_obj.instance = objects.Instance.obj_from_primitive(
                        jsonutils.loads(value))
        elif field == 'instance_metadata':
            setattr(req_obj, field, jsonutils.loads(value))
        else:
            setattr(req_obj, field, value)
    # This should never be a changed field
    req_obj.obj_reset_changes(['id'])
    return req_obj
