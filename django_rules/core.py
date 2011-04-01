from itertools import chain

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, F

from django_rules.models import RulePermission

class ObjectPermissionChecker(object):
    """
    Generic object permissions checker class being the heart of
    ``django-rules``.

    .. note::
       Once checked for single object, permissions are stored and we don't hit
       database again if another check is called for this object. This is great
       for templates, views or other request based checks (assuming we don't
       have hundreds of permissions on a single object as we fetch all
       permissions for checked object).

       On the other hand, if we call ``has_perm`` for perm1/object1, then we
       change permission state and call ``has_perm`` again for same
       perm1/object1 on same instance of ObjectPermissionChecker we won't see a
       difference as permissions are already fetched and stored within cache
       dictionary.
    """
    def __init__(self, user=None):
        """
        :param user_or_group: should be an ``User``, ``AnonymousUser`` or
          ``Group`` instance
        """
        self.user = user
        self._obj_perms_cache = {}

    def has_perm(self, perm, obj):
        """
        Checks if user/group has given permission for object.

        :param perm: permission as string, may or may not contain app_label
          prefix (if not prefixed, we grab app_label from ``obj``)
        :param obj: Django model instance for which permission should be checked

        """
        perm = perm.split('.')[-1]
        if self.user and not self.user.is_active:
            return False
        elif self.user and self.user.is_superuser:
            return True
        return perm in self.get_perms(obj)

    def get_perms(self, obj):
        """
        Returns list of ``codename``'s of all permissions for given ``obj``.

        :param obj: Django model instance for which permission should be checked

        """
        ctype = ContentType.objects.get_for_model(obj)
        key = self.get_local_cache_key(obj)
        if not key in self._obj_perms_cache:
            if self.user and not self.user.is_active:
                return []
            elif self.user and self.user.is_superuser:
                perms = list(chain(*RulePermission.objects
                    .filter(content_type=ctype)
                    .values_list("codename")))
            else:
                perms = []
                for rule in RulePermission.objects.filter(content_type=ctype):
                    if self.user.has_perm(rule.codename, obj):
                        perms.append(rule.codename)
            self._obj_perms_cache[key] = perms
        return self._obj_perms_cache[key]

    def get_local_cache_key(self, obj):
        """
        Returns cache key for ``_obj_perms_cache`` dict.
        """
        ctype = ContentType.objects.get_for_model(obj)
        return (ctype.id, obj.pk)
