# ----------------------------------------------------------------------------
# Copyright 2014 Nervana Systems Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ----------------------------------------------------------------------------
import logging
import sys
import numpy as np
import time
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))


class RNN(object):

    def __init__(self, layers, cost, update):
        """
        Create a RNN model.

        layers: List of recurrent layers
        cost:   Objective to minimize in fit()
        update: Update method for back prop

        """
        self.layers = layers
        self.cost = cost
        self.update_rule = update

    def fprop(self, x):
        for layer in self.layers:
            x = layer.fprop(x)
        return x

    def bprop(self):
        delta = self.cost.delta
        for layer in reversed(self.layers[:-1]):
            delta = layer.bprop(delta)
        return delta

    def update(self):
        params = []
        grads = []
        # these should be collected once at the beginning of fit
        # need to move grad buffers into __init__ first though
        for layer in self.layers:
            try:
                params.extend(layer.params)
                grads.extend(layer.grads)
            except AttributeError:
                pass

        self.update_rule.update(params, grads)

    def fit(self, dataset, num_epochs):
        logger.info("training")

        train_cost_list = []
        valid_cost_list = []

        for epoch in range(1, num_epochs+1):
            sys.stdout.write('\r')
            epoch_train_cost = []
            epoch_train_start = time.time()
            for batch in range(1, dataset.num_batches+1):
                x, y = dataset.next()
                y_pred = self.fprop(x)
                cost = self.cost(y_pred, y)

                # how should we handle this?
                from nervanagpu import GPUTensor
                if isinstance(cost, GPUTensor):
                    cost = cost.get()

                self.bprop()
                self.update()

                epoch_train_cost.append(cost)
                progress_bar = '=' * int(float(batch) / dataset.num_batches * 50)
                time_elapsed = time.time() - epoch_train_start
                progress_string = 'Train [{:<50}] {}/{} batches, {:.2f} cost, {:.2f} seconds'.format(
                    progress_bar, batch, dataset.num_batches, np.mean(epoch_train_cost), time_elapsed)

                sys.stdout.write('\r')
                sys.stdout.write(progress_string)
                sys.stdout.flush()

            sys.stdout.write('\r')
            sys.stdout.write(progress_string + '\n')

        return train_cost_list, valid_cost_list

    def get_params(self):
        np_params = dict()
        for i, ll in enumerate(self.layers):
            if hasattr(ll, 'params'):
                lkey = ll.__class__.__name__ + '_' + str(i)
                np_params[lkey] = ll.get_params()
        return np_params

    def set_params(self, params_dict):
        for i, ll in enumerate(self.layers):
            if hasattr(ll, 'params'):
                lkey = ll.__class__.__name__ + '_' + str(i)
                ll.set_params(params_dict[lkey])