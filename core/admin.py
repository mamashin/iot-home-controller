# -*- coding: utf-8 -*-

from django.contrib import admin
from django import forms
import json
from .models import MqttTopic, RcCode, MqttGroup


class PrettyJSONEncoder(json.JSONEncoder):
    def __init__(self, *args, indent, sort_keys, **kwargs):
        super().__init__(*args, indent=4, sort_keys=True, **kwargs)


class AliceDataJsonForm(forms.ModelForm):
    alice_data = forms.JSONField(encoder=PrettyJSONEncoder, initial=dict, required=False)


@admin.register(MqttGroup)
class MqttGroupAdmin(admin.ModelAdmin):
    list_display = ('group', )


@admin.register(MqttTopic)
class MqttTopicAdmin(admin.ModelAdmin):
    list_display_links = ('topic', )
    readonly_fields = ('str_id', )
    list_display = ('group', 'topic', 'description', 'unit_id', 'channel', 'alice', 'alice_data_count', 'alice_name',
                    'alice_room')
    form = AliceDataJsonForm
    search_fields = ('topic',  'description')
    list_filter = ('group', )


@admin.register(RcCode)
class RcCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'topic', 'description')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # When adding a new RC code, show the list only from certain groups (for example, relay)
        if db_field.name == "topic":
            kwargs["queryset"] = MqttTopic.objects.filter(group__group__in=['relay', ])
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
