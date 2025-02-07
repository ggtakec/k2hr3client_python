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
"""K2HR3 Python Client of Token API.

.. code-block:: python

    # Import modules from k2hr3client package.
    from k2hr3client.token import K2hr3Token
    from k2hr3client.http import K2hr3Http

    iaas_project = "demo"
    iaas_token = "gAAAAA..."
    mytoken = K2hr3Token(iaas_project, iaas_token)

    # POST a request to create a token to K2HR3 Token API.
    myhttp = K2hr3Http("http://127.0.0.1:18080")
    myhttp.POST(mytoken.create())
    mytoken.token  // gAAAAA...
"""

from enum import Enum
import json
import logging
from typing import Optional
import urllib.parse
import urllib.request


from k2hr3client.api import K2hr3Api, K2hr3HTTPMethod
from k2hr3client.exception import K2hr3Exception

LOG = logging.getLogger(__name__)

_TOKEN_API_CREATE_TOKEN_TYPE1 = """
{
    "auth": {
        "tenantName":      "<tenant name>",
        "passwordCredentials":    {
            "username":    "<user name>",
            "password":    "<pass phrase>"
        }
    }
}
"""
_TOKEN_API_CREATE_TOKEN_TYPE2 = """
{
    "auth": {
        "tenantName":      "<tenant name>"
    }
}
"""
IDENTITY_V3_PASSWORD_AUTH_JSON_DATA = """
{
    "auth": {
        "identity": {
            "methods": [
                "password"
            ],
            "password": {
                "user": {
                    "name": "admin",
                    "domain": {
                        "name": "Default"
                    },
                    "password": "devstacker"
                }
            } }
    }
}
"""
IDENTITY_V3_TOKEN_AUTH_JSON_DATA = """
{
    "auth": {
        "identity": {
            "methods": [
                "token"
            ],
            "token": {
                "id": ""
            }
        },
        "scope": {
            "project": {
                "domain": {
                    "id": "default"
                },
                "name": ""
            }
        }
    }
}
"""


class K2hr3AuthType(Enum):
    """Represent the type of authentication."""

    CREDENTIAL = 1
    TOKEN = 2


class K2hr3Token(K2hr3Api):  # pylint: disable=too-many-instance-attributes
    """Relationship with K2hr3 TOKEN API.

    See https://k2hr3.antpick.ax/api_token.html for details.
    """

    __slots__ = ('_tenant', '_openstack_token', )

    def __init__(self, iaas_project, iaas_token,
                 auth_type=K2hr3AuthType.TOKEN,
                 version=K2hr3Api.DEFAULT_VERSION):
        """Init the members.

        :param iaas_project: configuration file path
        :type iaas_project: str
        :raises K2hr3Exception: if invalid augments exist
        """
        super().__init__("user/tokens")
        self.iaas_project = iaas_project
        self.iaas_token = iaas_token

        # following attrs are dynamically set later.
        if auth_type == K2hr3AuthType.TOKEN:
            self.headers = {
                'Content-Type': 'application/json',
                'x-auth-token': 'U={}'.format(self._openstack_token)
            }
        elif auth_type == K2hr3AuthType.CREDENTIAL:
            self.headers = {
                'Content-Type': 'application/json'
            }
        self.body = None
        self.urlparams = None

        # optional attributes that are unique to this class
        self.user = None
        self.password = None

    # ---- POST/PUT ----
    # POST http(s)://API SERVER:PORT/v1/user/tokens
    # PUT http(s)://API SERVER:PORT/v1/user/tokens?urlarg
    def create(self, user=None, password=None):
        """Create tokens."""
        self.api_id = 1
        self.user = user
        self.password = password
        return self

    # ---- GET ----
    # GET http(s)://API SERVER:PORT/v1/user/tokens
    def show(self):
        """Show details of tokens."""
        self.api_id = 2
        return self

    # ---- HEAD ----
    # HEAD http(s)://API SERVER:PORT/v1/user/tokens
    def validate(self):
        """Validate tokens."""
        self.api_id = 3
        return self

    def __repr__(self):
        """Represent the instance."""
        attrs = []
        values = ""
        for attr in [
                '_tenant'
        ]:
            val = getattr(self, attr, None)
            if val:
                attrs.append((attr, repr(val)))
                values = ', '.join(['%s=%s' % i for i in attrs])
        return '<K2hr3Token ' + values + '>'

    @property  # type: ignore
    def iaas_project(self):
        """Return the k2hr3 tenant."""
        return self._tenant

    @iaas_project.setter
    def iaas_project(self, val):  # type: ignore # noqa: F811
        """Set the k2hr3 tenant."""
        if getattr(self, '_tenant', None) is None:
            self._tenant = val

    @property  # type: ignore
    def iaas_token(self):
        """Return the openstack token."""
        return self._openstack_token

    @iaas_token.setter
    def iaas_token(self, val):  # type: ignore # noqa: F811
        """Set the openstack token."""
        if getattr(self, '_openstack_token', None) is None:
            self._openstack_token = val

    @property
    def token(self):
        """Return k2hr3 token."""
        python_data = json.loads(self.resp.body)
        return python_data.get('token')

    #
    # abstract methos that must be implemented in subclasses
    #
    def _api_path(self, method: K2hr3HTTPMethod) -> Optional[str]:
        """Get the request url path."""
        if method == K2hr3HTTPMethod.POST:
            if self.api_id == 1:
                if self.user and self.password:
                    python_data = json.loads(_TOKEN_API_CREATE_TOKEN_TYPE1)
                    python_data['auth']['user'] = self.user
                    python_data['auth']['password'] = self.password
                    python_data['auth']['tenantName'] = self.iaas_project
                else:
                    python_data = json.loads(_TOKEN_API_CREATE_TOKEN_TYPE2)
                    python_data['auth']['tenantName'] = self.iaas_project
                self.body = json.dumps(python_data)
                return f'{self.version}/{self.basepath}'
        if method == K2hr3HTTPMethod.PUT:
            if self.api_id == 1:
                if self.user and self.password:
                    self.urlparams = json.dumps({
                        'user': self.user,
                        'password': self.password,
                        'tenantname': self.iaas_project
                    })
                else:
                    self.urlparams = json.dumps({
                        'tenantname': self.iaas_project
                    })
                return f'{self.version}/{self.basepath}'
        if method == K2hr3HTTPMethod.GET:
            if self.api_id == 2:
                return f'{self.version}/{self.basepath}'
        if method == K2hr3HTTPMethod.HEAD:
            if self.api_id == 3:
                return f'{self.version}/{self.basepath}'
        return None

    #
    # the other methods
    #
    @staticmethod
    def get_openstack_token(identity_url, user, password, project):
        """Get the openstack token."""
        # unscoped token-id
        # https://docs.openstack.org/api-ref/identity/v3/index.html#password-authentication-with-unscoped-authorization
        python_data = json.loads(IDENTITY_V3_PASSWORD_AUTH_JSON_DATA)
        python_data['auth']['identity']['password']['user']['name'] = user
        python_data['auth']['identity']['password']['user']['password'] = password  # noqa
        headers = {
            'User-Agent': 'k2hr3client-python',
            'Content-Type': 'application/json'
        }
        req = urllib.request.Request(identity_url,
                                     json.dumps(python_data).encode('ascii'),
                                     headers, method="POST")
        unscoped_token_id = ""
        with urllib.request.urlopen(req) as res:
            unscoped_token_id = dict(res.info()).get('X-Subject-Token')
        if not unscoped_token_id:
            return None

        # scoped token-id
        # https://docs.openstack.org/api-ref/identity/v3/index.html?expanded=#token-authentication-with-scoped-authorization
        python_data = json.loads(IDENTITY_V3_TOKEN_AUTH_JSON_DATA)
        python_data['auth']['identity']['token']['id'] = unscoped_token_id
        python_data['auth']['scope']['project']['name'] = project
        headers = {
            'User-Agent': 'k2hr3client-python',
            'Content-Type': 'application/json'
        }
        req = urllib.request.Request(identity_url,
                                     json.dumps(python_data).encode('ascii'),
                                     headers, method="POST")
        with urllib.request.urlopen(req) as res:
            scoped_token_id = dict(res.info()).get('X-Subject-Token')
            return scoped_token_id
        return None


class K2hr3RoleToken(K2hr3Api):  # pylint: disable=too-many-instance-attributes
    """Represent K2hr3 ROLE TOKEN API.

    See https://k2hr3.antpick.ax/api_role.html for details.
    """

    __slots__ = ('_r3token', '_role', '_expand')

    def __init__(self, r3token, role, expire):
        """Init the members."""
        super().__init__("role/token")
        self.r3token = r3token
        self.role = role
        # path should be "role/token/$roletoken".
        self.path = "/".join([self.basepath, self.role])
        self.expire = expire
        self.params = json.dumps({'expire': self._expire})
        self.headers = {
            'Content-Type': 'application/json',
            'x-auth-token': 'U={}'.format(self._r3token)
        }

    def __repr__(self):
        """Represent the instance."""
        attrs = []
        values = ""
        for attr in ['_r3token', '_role', '_expand']:
            val = getattr(self, attr, None)
            if val:
                attrs.append((attr, repr(val)))
                values = ', '.join(['%s=%s' % i for i in attrs])
        return '<K2hr3RoleToken ' + values + '>'

    @property  # type: ignore
    def role(self):
        """Return the role."""
        return self._role

    @role.setter
    def role(self, val):  # type: ignore # noqa: F811
        """Set the token."""
        if isinstance(val, str) is False:
            raise K2hr3Exception(f'value type must be str, not {type(val)}')
        if getattr(self, '_role', None) is None:
            self._role = val

    @property  # type: ignore
    def expire(self):
        """Return the expire."""
        return self._expire

    @expire.setter
    def expire(self, val):  # type: ignore # noqa: F811
        """Set the expire."""
        if isinstance(val, int) is False:
            raise K2hr3Exception(f'value type must be int, not {type(val)}')
        if getattr(self, '_expire', None) is None:
            self._expire = val

    @property  # type: ignore
    def r3token(self):
        """Return the r3token."""
        return self._r3token

    @r3token.setter
    def r3token(self, val):  # type: ignore # noqa: F811
        """Set the r3token."""
        if getattr(self, '_r3token', None) is None:
            self._r3token = val

    @property
    def token(self):
        """Return k2hr3 token."""
        python_data = json.loads(self.resp.body)
        return python_data.get('token')

    #
    # abstract methos that must be implemented in subclasses
    #
    def _api_path(self, method: K2hr3HTTPMethod) -> Optional[str]:
        """Get the request url path."""
        if method == K2hr3HTTPMethod.GET:
            return f'{self.version}/{self.path}'
        return None


class K2hr3RoleTokenList(K2hr3Api):  # pylint: disable=too-many-instance-attributes # noqa
    """Represent K2hr3 ROLE TOKEN LIST API.

    See https://k2hr3.antpick.ax/api_role.html for details.
    """

    __slots__ = ('_r3token', '_role', '_expand')

    def __init__(self, r3token, role, expand):
        """Init the members."""
        super().__init__("role/token/list")
        self.r3token = r3token
        self.role = role
        self.expand = expand

        # headers should include r3token
        self.headers = {
            'Content-Type': 'application/json',
            'x-auth-token': 'U={}'.format(self._r3token)
        }
        # path should be "role/token/$roletoken".
        self.path = "/".join([self.basepath, self.role])

    def __repr__(self):
        """Represent the instance."""
        attrs = []
        values = ""
        for attr in ['_r3token', '_role', '_expand']:
            val = getattr(self, attr, None)
            if val:
                attrs.append((attr, repr(val)))
                values = ', '.join(['%s=%s' % i for i in attrs])
        return '<K2hr3RoleTokenList ' + values + '>'

    @property  # type: ignore
    def role(self):
        """Return the role."""
        return self._role

    @role.setter
    def role(self, val):  # type: ignore # noqa: F811
        """Set the role."""
        if isinstance(val, str) is False:
            raise K2hr3Exception(f'value type must be str, not {type(val)}')
        if getattr(self, '_role', None) is None:
            self._role = val

    @property  # type: ignore
    def expand(self):
        """Return the expand."""
        return self._expand

    @expand.setter
    def expand(self, val):  # type: ignore # noqa: F811
        """Set the expand."""
        if isinstance(val, bool) is False:
            raise K2hr3Exception(f'value type must be bool, not {type(val)}')
        if getattr(self, '_expand', None) is None:
            self._expand = val

    @property  # type: ignore
    def r3token(self):
        """Return the r3token."""
        return self._r3token

    @r3token.setter
    def r3token(self, val):  # type: ignore # noqa: F811
        """Set the r3token."""
        if getattr(self, '_r3token', None) is None:
            self._r3token = val

    def registerpath(self, roletoken):
        """Set the registerpath."""
        python_data = json.loads(self.resp.body)
        return python_data['tokens'][roletoken]['registerpath']

    #
    # abstract methos that must be implemented in subclasses
    #
    def _api_path(self, method: K2hr3HTTPMethod) -> Optional[str]:
        """Get the request url path."""
        if method == K2hr3HTTPMethod.GET:
            return f'{self.version}/{self.path}'
        return None


#
# Local variables:
# tab-width: 4
# c-basic-offset: 4
# End:
# vim600: expandtab sw=4 ts=4 fdm=marker
# vim<600: expandtab sw=4 ts=4
#
