from django.db.models.fields import CharField, TextField
from django.db.models.signals import post_save, post_init, pre_delete

from .core import post_save_signal, post_init_signal, pre_delete_signal


# TODO.
class PoeditorComFieldMixin(object):
    pass


class PoeditorComCharField(CharField):
    def contribute_to_class(self, cls, name, *args, **kwargs):
        try:
            cls._poeditor_com_field_fields.append(name)
        except AttributeError:
            cls._poeditor_com_field_fields = [name]
            post_save.connect(post_save_signal, sender=cls)
            post_init.connect(post_init_signal, sender=cls)
            pre_delete.connect(pre_delete_signal, sender=cls)

        return super(PoeditorComCharField, self).contribute_to_class(
            cls, name, *args, **kwargs)


class PoeditorComTextField(TextField):
    def contribute_to_class(self, cls, name, *args, **kwargs):
        try:
            cls._poeditor_com_field_fields.append(name)
        except AttributeError:
            cls._poeditor_com_field_fields = [name]
            post_save.connect(post_save_signal, sender=cls)
            post_init.connect(post_init_signal, sender=cls)
            pre_delete.connect(pre_delete_signal, sender=cls)

        return super(PoeditorComTextField, self).contribute_to_class(
            cls, name, *args, **kwargs)
