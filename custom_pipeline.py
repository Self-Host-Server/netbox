from django.contrib.auth.models import Group


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
    user.is_superuser = "superusers" in groups
    user.is_staff = "staff" in groups
    user.save()
