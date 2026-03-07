from social_core.exceptions import AuthForbidden

from users.models import Group

ALLOWED_GROUPS = {"Netbox_Users", "Netbox_Admins"}


def check_allowed_groups(response, backend, *args, **kwargs):
    groups = set(response.get("groups", []) or [])
    if not groups & ALLOWED_GROUPS:
        raise AuthForbidden(backend)


def add_groups(response, user, backend, *args, **kwargs):
    groups = response.get("groups", []) or []
    for name in groups:
        group, _ = Group.objects.get_or_create(name=name)
        user.groups.add(group)


def remove_groups(response, user, backend, *args, **kwargs):
    groups = response.get("groups")
    if not groups:
        user.groups.clear()
        return

    keep = set(groups)
    for g in list(user.groups.all()):
        if g.name not in keep:
            user.groups.remove(g)


def set_roles(response, user, backend, *args, **kwargs):
    groups = set(response.get("groups", []) or [])
    user.is_superuser = "Netbox_Admins" in groups
    user.is_staff = "Netbox_Admins" in groups
    user.save()
