import pdb
import numpy as np
class Crossentropy(object):

    def __init__(self, input_size, batch_size, seq_length, backend, dtype=np.float32):
        self.input_size = input_size
        self.seq_length = seq_length
        self.batch_size = batch_size
        self.backend = backend
        self.dtype = dtype
        self.cost = self.backend.zeros((1, 1), dtype=self.dtype)
        self.delta = self.backend.zeros((input_size * seq_length, batch_size), dtype=self.dtype)

    def __call__(self, X, Y):

        cost_buffer = self.backend.zeros((self.seq_length, self.batch_size), dtype=self.dtype)

        for step in range(self.seq_length):
            # slice
            start = step * self.input_size
            end = (step+1) * self.input_size
            x = X[start:end]
            y = Y[start:end]

            cost = cost_buffer[step].reshape((1, self.batch_size))
            delta = self.delta[start:end]

            # delta
            self.backend.add(x, 0, delta)
            self.backend.subtract(delta, y, delta)

            # cost
            temp_cost_buffer = self.backend.zeros(x.shape, dtype=self.dtype)
            self.backend.add(x, 1e-20, x)
            self.backend.multiply(x, y, temp_cost_buffer)

            # cost isn't being sliced into a 2d
            temp = self.backend.zeros((1, self.batch_size), dtype=self.dtype)
            temp2 = self.backend.zeros((1, 1), dtype=self.dtype)
            self.backend.max(temp_cost_buffer, 0, out=temp)
            self.backend.add(temp, 1e-10, temp)
            self.backend.log(temp, temp)
            self.backend.sum(temp, 1, out=temp2)
            self.backend.add(temp2, self.cost, self.cost)

        self.backend.multiply(self.cost, -1, self.cost)
        self.backend.divide(self.cost, self.batch_size, self.cost)
        self.backend.divide(self.cost, self.seq_length, self.cost)
        return self.cost