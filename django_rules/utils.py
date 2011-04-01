# -*- coding: utf-8 -*-

import sys

from django.contrib.contenttypes.models import ContentType

from models import RulePermission

rules = set()

def register(app_name, codename, model, field_name='', view_param_pk='', description='', name=''):
    """
    Call this function in your rules.py to register your RulePermissions
    All registered rules will be synced when sync_rules command is run
    """
    # We get the `ContentType` for that `model` within that `app_name`
    try:
        ctype = ContentType.objects.get(app_label=app_name, model=model.lower())
    except ContentType.DoesNotExist:
        sys.stderr.write('! Rule codenamed %s will not be synced as model %s was not found for app %s\n' % (codename, model, app_name))
        return

    rule, created = RulePermission.objects.get_or_create(codename=codename, content_type=ctype, defaults=dict(field_name=field_name,
                view_param_pk=view_param_pk, description=description, name=name))

    perm = '%s.%s' % (app_name, codename)

    if perm in rules:
        sys.stderr.write('Careful rule %s being overwritten. Make sure its codename is not repeated in other rules.py files\n' % codename)

    rules.add(perm)
