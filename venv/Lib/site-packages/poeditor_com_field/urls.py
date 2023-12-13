# -*- coding: utf-8 -*-
from django.conf.urls import url
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    url(
        regex="^BloomFilter/~create/$",
        view=views.BloomFilterCreateView.as_view(),
        name='BloomFilter_create', ),
    url(
        regex="^BloomFilter/(?P<pk>\d+)/~delete/$",
        view=views.BloomFilterDeleteView.as_view(),
        name='BloomFilter_delete', ),
    url(
        regex="^BloomFilter/(?P<pk>\d+)/$",
        view=views.BloomFilterDetailView.as_view(),
        name='BloomFilter_detail', ),
    url(
        regex="^BloomFilter/(?P<pk>\d+)/~update/$",
        view=views.BloomFilterUpdateView.as_view(),
        name='BloomFilter_update', ),
    url(
        regex="^BloomFilter/$",
        view=views.BloomFilterListView.as_view(),
        name='BloomFilter_list', ),
]
