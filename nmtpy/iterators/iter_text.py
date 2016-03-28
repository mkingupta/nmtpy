#!/usr/bin/env python
from six.moves import range
from six.moves import zip

from collections import OrderedDict

import random
import numpy as np

from ..sysutils import fopen
from ..nmtutils import mask_data

"""Single side text iterator for monolingual data."""
class TextIterator(object):
    def __init__(self, data, _dict, batch_size, n_words=0, data_name='x', do_mask=False):

        random.seed(1234)

        self.data = data
        self.dict = _dict
        self.batch_size = batch_size
        self.n_words = n_words
        self.data_name = data_name

        self.n_samples = 0

        self.__seqs = []
        self.__idxs = []
        self.__minibatches = []
        self.__return_keys = [data_name]
        self.__iter = None

        self.do_mask = do_mask
        if self.do_mask:
            self.__return_keys.append("%s_mask" % data_name)

        # Directly read it
        self.read()

    def set_batch_size(self, bs):
        self.batch_size = bs
        self.prepare_batches()

    def rewind(self):
        self.__iter = iter(self.__minibatches)

    def __iter__(self):
        return self

    def get_idxs(self):
        return self.__idxs

    def set_blackout(self, prob):
        pass

    def read(self):
        self.__seqs = []
        self.__idxs = []
        #self.__max_filt = 0
        with fopen(self.data, 'r') as f:
            for idx, line in enumerate(f):
                line = line.strip()

                # Skip empty lines
                if line != "":
                    line = line.split(" ")

                    seq = [self.dict.get(w, 1) for w in line]

                    # if given limit vocabulary
                    if self.n_words > 0:
                        seq = [w if w < self.n_words else 1 for w in seq]

                    # Append the sequence
                    self.__seqs += [seq]

                    # Keep line order of the accepted phrases in a list
                    self.__idxs += [idx]

        self.n_samples = len(self.__idxs)

    def prepare_batches(self):
        sample_idxs = np.arange(self.n_samples)
        self.__minibatches = []

        for i in range(0, self.n_samples, self.batch_size):
            batch_idxs = sample_idxs[i:i + self.batch_size]
            x, x_mask = mask_data([self.__seqs[i] for i in batch_idxs])
            self.__minibatches.append((batch_idxs, x, x_mask))

        self.__iter = iter(self.__minibatches)
        self.__idxs = sample_idxs

    def next(self):
        try:
            data = next(self.__iter)
        except StopIteration as si:
            self.rewind()
            raise
        except AttributeError as ae:
            raise Exception("You need to call prepare_batches() first.")
        else:
            return OrderedDict([(k,data[i+1]) for i,k in enumerate(self.__return_keys)])
