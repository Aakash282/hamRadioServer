import numpy as np
class Affine(object):

    def __init__(self, input_size, output_size, batch_size, seq_length, init, backend, dtype=np.float32):
        self.input_size = input_size
        self.output_size = output_size
        self.batch_size = batch_size
        self.seq_length = seq_length
        self.backend = backend
        self.dtype = dtype

        self.W = self.backend.array(init((output_size, input_size)), dtype=self.dtype)
        self.b = self.backend.array(init((output_size, 1)), dtype=self.dtype)
        self.params = [self.W, self.b]

    def get_params(self):
        return [x.asnumpyarray()for x in self.params]

    def set_params(self, params):
        for param, set_param in zip(self.params, params):
            param[:] = set_param

    def fprop(self, X):
        self.X = X

        self.W_buffer = self.backend.zeros((self.output_size * self.seq_length, self.batch_size), dtype=self.dtype)

        for step in range(self.seq_length):
            x = X[step * self.input_size:(step+1) * self.input_size]
            W_buffer = self.W_buffer[step * self.output_size:(step+1) * self.output_size]
            self.backend.dot(self.W, x, W_buffer)
            self.backend.add(W_buffer, self.b, W_buffer)

        return self.W_buffer

    def bprop(self, delta):

        self.delta = self.backend.zeros((self.input_size * self.seq_length, self.batch_size), dtype=self.dtype)

        self.W_delta = self.backend.zeros(self.W.shape, dtype=self.dtype)
        self.b_delta = self.backend.zeros(self.b.shape, dtype=self.dtype)
        self.grads = [self.W_delta, self.b_delta]

        for step in reversed(range(self.seq_length)):
            # slice
            in_delta = delta[step * self.output_size:(step+1) * self.output_size]
            out_delta = self.delta[step * self.input_size:(step+1) * self.input_size]
            x = self.X[step * self.input_size:(step+1) * self.input_size]

            # accumulate W_deltas
            W_delta_buffer = self.backend.zeros(self.W_delta.shape, dtype=self.dtype)
            self.backend.dot(in_delta, x.transpose(), W_delta_buffer)
            self.backend.add(W_delta_buffer, self.W_delta, self.W_delta)

            # accumulate b_deltas
            b_delta_buffer = self.backend.zeros(self.b_delta.shape, dtype=self.dtype)
            self.backend.sum(in_delta, 1, b_delta_buffer)
            self.backend.add(b_delta_buffer, self.b_delta, self.b_delta)

            # delta
            self.backend.dot(self.W.transpose(), in_delta, out_delta)

        self.backend.divide(self.W_delta, self.batch_size, self.W_delta)
        self.backend.divide(self.b_delta, self.batch_size, self.b_delta)
        return self.delta
