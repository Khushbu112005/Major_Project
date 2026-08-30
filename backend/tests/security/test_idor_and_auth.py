"""
Security Tests: Authorization & IDOR Defenses.
"""

import pytest
from backend.app.common.security import AuthContext, check_object_ownership
from backend.app.common.errors import ForbiddenException


def test_idor_protection_blocks_other_user_resource():
    citizen_auth = AuthContext(user_id="usr_citizen_1", email="c1@test.org", role="citizen")

    # Accessing own resource -> PASS
    check_object_ownership(citizen_auth, resource_owner_id="usr_citizen_1", resource_type="document")

    # Accessing another user's private resource -> FORBIDDEN
    with pytest.raises(ForbiddenException):
        check_object_ownership(citizen_auth, resource_owner_id="usr_victim_2", resource_type="document")


def test_admin_bypass_for_maintenance():
    admin_auth = AuthContext(user_id="usr_admin_1", email="admin@test.org", role="admin")
    # Admin can inspect any resource
    check_object_ownership(admin_auth, resource_owner_id="usr_victim_2", resource_type="document")
