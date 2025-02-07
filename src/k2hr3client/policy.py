# -*- coding: utf-8 -*-
#
# K2HDKC DBaaS based on Trove
#
# Copyright 2020 Yahoo Japan Corporation
# Copyright 2024 LY Corporation
#
# K2HDKC DBaaS is a Database as a Service compatible with Trove which
# is DBaaS for OpenStack.
# Using K2HR3 as backend and incorporating it into Trove to provide
# DBaaS functionality. K2HDKC, K2HR3, CHMPX and K2HASH are components
# provided as AntPickax.
#
# For the full copyright and license information, please view
# the license file that was distributed with this source code.
#
# AUTHOR:   Hirotaka Wakabayashi
# CREATE:   Mon Sep 14 2020
# REVISION:
#
#
"""K2HR3 Python Client of Policy API.

.. code-block:: python

    # Import modules from k2hr3client package.
    from k2hr3client.token import K2hr3Token
    from k2hr3client.http import K2hr3Http
    from k2hr3client.policy import K2hr3Policy

    iaas_project = "demo"
    iaas_token = "gAAAAA..."
    mytoken = K2hr3Token(iaas_project, iaas_token)

    # POST a request to create a token to K2HR3 Token API.
    myhttp = K2hr3Http("http://127.0.0.1:18080")
    myhttp.POST(mytoken.create())
    mytoken.token  // gAAAAA...

    # POST request to get a K2HR3 Policy API.
    mypolicy = K2hr3Policy(mytoken.token)
    RESOURCE_PATH = "yrn:yahoo:::demo:resource:test_resource"
    myhttp.POST(
        mypolicy.create(
            policy_name="test_policy",
            effect="allow",
            action=['yrn:yahoo::::action:read'],
            resource=[RESOURCE_PATH],
            condition=None,
            alias=[]
            )
        )
    mypolicy.resp.body // {"result":true...

"""

import json
import logging
from typing import List, Optional


from k2hr3client.api import K2hr3Api, K2hr3HTTPMethod

LOG = logging.getLogger(__name__)

_POLICY_API_CREATE_POLICY = """
{
    "policy":    {
        "name":      "<policy name>",
        "effect":    "<allow or deny>",
        "action":    [],
        "resource":  [],
        "condition": null,
        "alias":     []
    }
}
"""


class K2hr3Policy(K2hr3Api):  # pylint: disable=too-many-instance-attributes
    """Relationship with K2HR3 POLICY API.

    See https://k2hr3.antpick.ax/api_policy.html for details.
    """

    __slots__ = ('_r3token',)

    def __init__(self, r3token: str) -> None:
        """Init the members."""
        super().__init__("policy")
        self.r3token = r3token

        # following attrs are dynamically set later.
        if r3token:
            self.headers = {
                'Content-Type': 'application/json',
                'x-auth-token': 'U={}'.format(self._r3token)
            }
        else:
            self.headers = {
                'Content-Type': 'application/json',
            }
        self.body = None
        self.urlparams = None
        # attributes that are unique to this class
        self.policy_name = None
        self.effect = None
        self.action = None
        self.resource = None
        self.condition = None
        self.alias = None
        self.service = None
        self.tenant = None

    # ---- POST/PUT ----
    # POST   http(s)://API SERVER:PORT/v1/policy
    # PUT    http(s)://API SERVER:PORT/v1/policy?urlarg
    def create(self, policy_name: str, effect: str,
               action: Optional[List[str]],
               resource: Optional[List[str]] = None,
               condition: Optional[str] = None,
               alias: Optional[List[str]] = None):
        """Create policies."""
        self.api_id = 1
        # must to process a request further
        self.policy_name = policy_name  # type: ignore
        self.effect = effect  # type: ignore
        self.action = action  # type: ignore
        # optionals
        self.resource = resource  # type: ignore
        self.condition = condition  # type: ignore
        self.alias = alias  # type: ignore
        return self

    # ---- GET ----
    # GET    http(s)://API SERVER:PORT/v1/policy/\
    #            policy path or yrn full policy path{?service=service name} # noqa
    def get(self, policy_name: str, service: str):
        """Get policies."""
        self.api_id = 3
        self.policy_name = policy_name   # type: ignore
        self.service = service  # type: ignore
        return self

    # ---- HEAD ----
    # HEAD   http(s)://API SERVER:PORT/v1/policy/yrn full policy path?urlarg
    def validate(self, policy_name: str, tenant: str, resource: str,
                 action: str, service: Optional[str] = None):
        """Validate policies."""
        self.api_id = 4
        self.policy_name = policy_name  # type: ignore
        self.tenant = tenant  # type: ignore
        self.resource = resource  # type: ignore
        self.action = action  # type: ignore
        # optionals
        self.service = service  # type: ignore
        return self

    # ---- DELETE ----
    # DELETE http(s)://API SERVER:PORT/v1/policy/policy path or yrn full policy path # noqa
    def delete(self, policy_name: str):
        """Delete policies."""
        self.api_id = 5
        self.policy_name = policy_name  # type: ignore
        return self

    def __repr__(self) -> str:
        """Represent the instance."""
        attrs = []
        values = ""
        for attr in [
                '_r3token'
        ]:
            val = getattr(self, attr, None)
            if val:
                attrs.append((attr, repr(val)))
                values = ', '.join(['%s=%s' % i for i in attrs])
        return '<K2hr3Policy ' + values + '>'

    @property  # type: ignore
    def r3token(self) -> str:
        """Return the r3token."""
        return self._r3token

    @r3token.setter
    def r3token(self, val: str) -> None:  # type: ignore # noqa: F811
        """Set the r3token."""
        if getattr(self, '_r3token', None) is None:
            self._r3token = val

    #
    # abstract methos that must be implemented in subclasses
    #
    def _api_path(self, method: K2hr3HTTPMethod) -> Optional[str]:
        """Get the request url path."""
        if method == K2hr3HTTPMethod.POST:
            if self.api_id == 1:
                python_data = json.loads(_POLICY_API_CREATE_POLICY)
                python_data['policy']['name'] = self.policy_name
                python_data['policy']['effect'] = self.effect
                python_data['policy']['action'] = self.action
                python_data['policy']['resource'] = self.resource
                python_data['policy']['alias'] = self.alias
                self.body = json.dumps(python_data)
                return f'{self.version}/{self.basepath}'
        if method == K2hr3HTTPMethod.PUT:
            if self.api_id == 1:
                self.urlparams = json.dumps({
                    'name': self.policy_name,
                    'effect': self.effect,
                    'action': self.action,
                    'resource': self.resource,
                    'alias': self.alias
                })
                return f'{self.version}/{self.basepath}'
        if method == K2hr3HTTPMethod.GET:
            if self.api_id == 3:
                self.urlparams = json.dumps({
                    'service': self.service
                })
                return f'{self.version}/{self.basepath}/{self.policy_name}'
        if method == K2hr3HTTPMethod.HEAD:
            if self.api_id == 4:
                self.urlparams = json.dumps({
                    'tenant': self.tenant,
                    'resource': self.resource,
                    'action': self.action,
                    'service': self.service
                })
                return f'{self.version}/{self.basepath}/{self.policy_name}'
        if method == K2hr3HTTPMethod.DELETE:
            if self.api_id == 5:
                return f'{self.version}/{self.basepath}/{self.policy_name}'
        return None

#
# Local variables:
# tab-width: 4
# c-basic-offset: 4
# End:
# vim600: expandtab sw=4 ts=4 fdm=marker
# vim<600: expandtab sw=4 ts=4
#
