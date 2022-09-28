from typing import Union
from flask_login import UserMixin
from apps.models.auth import User

from apps.utils.perms import has_permission_flags


class SessionUser(UserMixin):
    def __init__(self, record: User):
        super().__init__()
        # self.record = record
        self.id = record.id
        self.email = record.email
        self.username = record.username
        self.permissions = record.permissions
        self.role = record.role
        # self.reviewer = record.reviewer
        # self.role = 0000
    def has_permissions(self, flags: Union[list, int]):
        return has_permission_flags(flags, self.permissions)
