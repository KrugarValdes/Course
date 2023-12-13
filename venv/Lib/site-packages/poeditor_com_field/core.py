from collections import namedtuple
from copy import deepcopy
import json

from celery.task.base import task
from celery.task.base import periodic_task
from celery.schedules import crontab
import requests

from django.conf import settings
from django.db.transaction import atomic
from django.core.validators import EMPTY_VALUES
from django.db.models.loading import get_models

import logging
logger = logging.getLogger(__name__)

from .models import Link

Term = namedtuple('Term', 'field_name,value,reference')


def post_init_signal(sender, instance=None, **kwargs):
    instance._poeditor_com_field_cache = deepcopy(instance)


def post_save_signal(sender, created=None, instance=None, **kwargs):
    update_terms(instance, created)


def pre_delete_signal(sender, instance=None, **kwargs):
    remove_terms(instance)


def link_add(term):
    Link.objects.select_for_update().filter(term=term)
    try:
        link = Link.objects.get(term=term.value)
        if term.reference in link.references:
            return None
        else:
            link.count += 1
            link.references += term.reference
            link.save()
            return link
    except Link.DoesNotExist:
        return Link.objects.create(
            term=term.value, count=1, references=term.reference)


def link_subtract(term):
    Link.objects.select_for_update().filter(term=term)
    try:
        link = Link.objects.get(
            term=term.value, )
        link.count -= 1
        link.references.replace(term.reference, '')
        link.save()
        return link
    except Link.DoesNotExist:
        return None


def changed_terms(instance, created):
    deleted, added = [], []
    for field_name in instance._poeditor_com_field_fields:

        if not created:
            before = make_term(instance._poeditor_com_field_cache, field_name)
        after = make_term(instance, field_name)

        if not created and before.value == after.value:
            continue

        if not created and before.value not in EMPTY_VALUES:
            deleted.append(before)

        if after.value not in EMPTY_VALUES:
            added.append(after)

    return deleted, added


def make_term(instance, field_name):
    return Term(
        field_name,
        getattr(instance, field_name),
        u'<{}.{} id={} field={} />'.format(instance._meta.app_label,
                                           instance.__class__.__name__,
                                           instance.pk, field_name), )


@atomic
def update_terms(instance, created):
    deleted, added = changed_terms(instance, created)
    modified_link_pks = set()
    if added:
        modified_link_pks |= set(
            link_add(x).pk for x in added if x is not None)
    if deleted:
        modified_link_pks |= set(
            link_subtract(x).pk for x in deleted if x is not None)

    sync_links(list(modified_link_pks))


@atomic
def remove_terms(instance):
    terms = [
        make_term(instance, x) for x in instance._poeditor_com_field_fields
    ]
    modified_link_pks = set(
        link_subtract(x).pk for x in terms if x is not None)
    sync_links(list(modified_link_pks))


def post(path, data):
    r = requests.post(
        'https://api.poeditor.com/v2/' + path,
        data={
            'id': settings.POEDITOR_PROJECT_ID,
            'api_token': settings.POEDITOR_API_TOKEN,
            'data': json.dumps(data).replace("\\r", ""),
        }, )
    try:
        response = r.json()
        if ('response' in response and 'status' in response['response'] and
                response['response']['status'] == 'success'):
            logger.info(u"Succes: path='{}'".format(path))
            return True, response
        else:
            logger.error(
                u"Error: path='{}', response='{}'".format(path, r.text))
            return False, response
    except ValueError:
        logger.error(u"Error: path='{}', response='{}'".format(path, r.text))
        return False, None


@task
def sync_links(link_pks=None):
    links = Link.objects.filter(pk__in=link_pks)

    if not links:
        return

    add = links.filter(count__gt=0, exists_on_server=False)
    len(add)  # Force evaluation.
    update = links.filter(count__gt=0, exists_on_server=True)
    len(update)  # Force evaluation.
    delete = links.filter(count__lt=1, exists_on_server=True)
    len(delete)  # Force evaluation.

    if add:
        with atomic():
            add.select_for_update().update(in_sync_with_server=False)
            status, _ = post('terms/add', [{
                "term": x.term,
                "context": settings.POEDITOR_CONTEXT,
                "reference": x.references,
            } for x in add])
            if status:
                add.update(exists_on_server=True, in_sync_with_server=True)

    if update:
        with atomic():
            update.select_for_update().update(in_sync_with_server=False)
            status, _ = post('terms/update', [{
                "term": x.term,
                "context": settings.POEDITOR_CONTEXT,
                "reference": x.references,
            } for x in update])
            if status:
                update.update(in_sync_with_server=True)

    if delete:
        with atomic():
            delete.select_for_update().update(in_sync_with_server=False)
            status, _ = post('terms/delete', [{
                "term": x.term,
                "context": settings.POEDITOR_CONTEXT,
            } for x in delete])
            if status:
                delete.update(in_sync_with_server=True)
                delete.delete()


def sync_existing_models():
    for model in get_models():
        try:
            fields = model._poeditor_com_field_fields
        except AttributeError:
            continue

        link_pks = []
        for obj in model.objects.all():
            for field in fields:
                term = make_term(obj, field)
                link = link_add(term)
                if link is not None:
                    link_pks.append(link.pk)

            sync_links(link_pks)


@periodic_task(run_every=crontab(minute=5))
def retry_sync_links():
    logger.info("Cronjob: retry_sync_links called.")
    sync_links(
        Link.objects.filter(in_sync_with_server=False).values_list(
            'pk', flat=True))
