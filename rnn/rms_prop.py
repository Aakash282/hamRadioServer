import numpy as np

class RMSProp(object):

    def __init__(self, backend, dtype=np.float32):
        self.backend = backend
        self.dtype = dtype
        self.decay_rate = 0.999
        self.learning_rate = 1e-3
        self.state_list = None
        self.epsilon = 1e-6

    def update(self, param_list, grad_list):

        if not self.state_list:
            self.state_list = []
            for param in param_list:
                self.state_list.append(self.backend.zeros(param.shape, dtype=self.dtype))

        for param, grad, state in zip(param_list, grad_list, self.state_list):
            # gradient clipping
            self.backend.clip(grad, -5, 5, grad)

            # update state
            squared_grad = self.backend.zeros(grad.shape, dtype=self.dtype)
            self.backend.multiply(self.decay_rate, state, state)
            self.backend.square(grad, squared_grad)
            self.backend.multiply(squared_grad, 1.0-self.decay_rate, squared_grad)
            self.backend.add(squared_grad, state, state)

            # compute update
            update = self.backend.zeros(param.shape, dtype=self.dtype)
            state_root = self.backend.zeros(state.shape, dtype=self.dtype)
            self.backend.add(state, self.epsilon, state_root)
            self.backend.sqrt(state_root, state_root)
            self.backend.multiply(grad, self.learning_rate, update)

        # adding epsilon here since state_root has zeros
        # ideally we should adjust the epsilon added to state
        self.backend.add(state_root, self.epsilon, state_root)

        self.backend.divide(update, state_root, update)

        # update
        self.backend.subtract(param, update, param)
