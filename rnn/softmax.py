import pdb
import numpy as np
class Softmax(object):

    def __init__(self, size, batch_size, seq_length, backend, dtype=np.float32):
        # hyper parameters
        self.size = size
        self.batch_size = batch_size
        self.seq_length = seq_length
        self.backend = backend
        self.dtype = dtype
        
    def fprop(self, X):

        self.buffer = self.backend.zeros((self.size * self.seq_length, self.batch_size), dtype=self.dtype)

        self.X = X

        for step in range(self.seq_length):
            start = step * self.size
            end = (step+1) * self.size
            x = X[start:end]
            buffer = self.buffer[start:end]

            from nervanagpu import NervanaGPU
            if isinstance(self.backend, NervanaGPU):
                buffer[:] = (self.backend.reciprocal(self.backend.sum(
                      self.backend.exp(x - self.backend.max(x, axis=0)), axis=0)) *
                      self.backend.exp(x - self.backend.max(x, axis=0)))
            else:
                self.backend.softmax(x, buffer)

        return self.buffer
