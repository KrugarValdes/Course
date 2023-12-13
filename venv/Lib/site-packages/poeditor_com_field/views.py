# -*- coding: utf-8 -*-
from django.views.generic import (CreateView, DeleteView, DetailView,
                                  UpdateView, ListView)

from .models import (
    BloomFilter, )


class BloomFilterCreateView(CreateView):

    model = BloomFilter


class BloomFilterDeleteView(DeleteView):

    model = BloomFilter


class BloomFilterDetailView(DetailView):

    model = BloomFilter


class BloomFilterUpdateView(UpdateView):

    model = BloomFilter


class BloomFilterListView(ListView):

    model = BloomFilter
