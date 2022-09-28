from typing import Union

IS_ADMIN = 1<<4

def has_permission_flags(flags: Union[list, int], permissions: Union[list, int]):
    flags = sum(flags) if type(flags) == list else flags
    permissions = sum(permissions) if type(permissions) == list else permissions
    return flags & permissions == flags

# testing
'''
assert(has_permissions_flag([IS_ADMIN], IS_ADMIN))
assert(has_permissions_flag([1<<2, 1<<3], 1<<3|1<<2|1<<1|1<<0))
assert(has_permissions_flag([1<<2, 1<<3], 1<<3|1<<4|1<<1|1<<0)==False)
'''