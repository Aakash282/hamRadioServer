import numpy as np

class LSTM(object):

    def __init__(self, input_size, output_size, batch_size, seq_length, init, backend):
        self.input_size = input_size
        self.output_size = output_size
        self.batch_size = batch_size
        self.seq_length = seq_length
        self.backend = backend

        self.gate_activation = backend.sig
        self.gate_activation_deriv = lambda x: backend.sig(x) * (1.0 - backend.sig(x))

        self.activation = backend.tanh
        self.activation_deriv = lambda x: -backend.square(backend.clip(backend.tanh(x), -10.0, 10.0)) + 1.0


        weight_sz = output_size * 4
        self.weight_buf = backend.array(init((input_size + output_size, weight_sz)), dtype=np.float32)
        self.W = self.weight_buf[:input_size]
        self.H = self.weight_buf[input_size:]
        # self.W = backend.array(init((output_size * 4, input_size)))
        # self.H = backend.array(init((output_size * 4, output_size)))

        self.bias_buf = backend.array(init((2 * weight_sz, 1)), dtype=np.float32)
        self.b = self.bias_buf[:weight_sz]
        self.v = self.bias_buf[weight_sz:]
        # self.b = backend.array(init((output_size * 4, 1)))
        # self.v = backend.array(init((output_size * 4, 1)))
        self.params = [self.W, self.H, self.b, self.v]

        # deltas
        self.weight_delta_buf = backend.zeros(self.weight_buf.shape, dtype=np.float32)
        self.W_delta = self.weight_delta_buf[:input_size]
        self.H_delta = self.weight_delta_buf[input_size:]

        self.bias_delta_buf = backend.zeros(self.bias_buf.shape, dtype=np.float32)
        self.b_delta = self.bias_delta_buf[:weight_sz]
        self.v_delta = self.bias_delta_buf[weight_sz:]

        self.grads = [self.W_delta, self.H_delta, self.b_delta, self.v_delta]

        # Gate and Act buffers
        cell_sz = self.output_size * self.seq_length
        gate_act_sz = cell_sz * 4
        self.gate_act_buffer = self.backend.zeros((gate_act_sz * 2, self.batch_size), dtype=np.float32)
        self.gate_buffer = self.gate_act_buffer[:gate_act_sz]
        self.act_buffer = self.gate_act_buffer[gate_act_sz:]

        # Cell buffers
        self.cell_buffer = self.backend.zeros((cell_sz * 2, self.batch_size), dtype=np.float32)
        self.c_buffer = self.cell_buffer[:cell_sz]
        self.h_buffer = self.cell_buffer[cell_sz:]

        # BPROP buffers
        self.gate_act_delta = self.backend.zeros((gate_act_sz * 2, self.batch_size), dtype=np.float32)
        self.gate_delta = self.gate_act_delta[:gate_act_sz]
        self.act_delta = self.gate_act_delta[gate_act_sz:]

        self.cell_delta = self.backend.zeros((cell_sz * 2, self.batch_size), dtype=np.float32)
        self.c_delta = self.cell_delta[:cell_sz]
        self.h_delta = self.cell_delta[cell_sz:]

        # How should we name this vs. bprop
        self.delta = self.backend.zeros((self.input_size * self.seq_length, self.batch_size), dtype=np.float32)

        self.init_views()
    #TODO - Creating and recreating all these views can add overhead to nervanagpu
    #       should just unroll all the views into persistent tensors the first time

    def init_views(self):
        osz = self.output_size
        isz = self.input_size

        self.fprop_views = [None for i in range(self.seq_length)]

        for step in range(self.seq_length):
            stepview = dict()

            start      = step * osz
            end        = start + osz
            prev_start = start - osz
            prev_end   = None if step == 0 else start  # For wrapping around

            stepview['c'] = self.c_buffer[start:end]
            stepview['h'] = self.h_buffer[start:end]
            stepview['prev_c'] = self.c_buffer[prev_start:prev_end]
            stepview['prev_h'] = self.h_buffer[prev_start:prev_end]

            idxs = np.arange(5) * osz + start * 4

            stepview['gate_buf']  = self.gate_buffer[idxs[0]:idxs[4]]
            stepview['act_buf']   = self.act_buffer[idxs[0]:idxs[4]]
            stepview['gates']     = self.act_buffer[idxs[0]:idxs[3]]
            stepview['in_xform']  = self.act_buffer[idxs[3]:idxs[4]]
            stepview['g_in']      = self.act_buffer[idxs[0]:idxs[1]]
            stepview['g_forget']  = self.act_buffer[idxs[1]:idxs[2]]
            stepview['g_out']     = self.act_buffer[idxs[2]:idxs[3]]


            stepview['c_del']       = self.c_delta[start:end]
            stepview['h_del']       = self.h_delta[start:end]
            stepview['prev_c_del']  = self.c_delta[prev_start:start]
            stepview['out_del']     = self.delta[step * isz:(step+1) * isz]

            # slice pre-activation gates
            stepview['pre_gates']    = self.gate_buffer[idxs[0]:idxs[3]]
            stepview['pre_in_xform'] = self.gate_buffer[idxs[3]:idxs[4]]

            # slice pre-activation gate deltas
            stepview['gate_del']     = self.gate_delta[start*4:end*4]
            stepview['gates_del']    = self.gate_delta[idxs[0]:idxs[3]]
            stepview['in_xform_del'] = self.gate_delta[idxs[3]:idxs[4]]

            # slice post-activation gate deltas
            stepview['act_gates_del']    = self.act_delta[idxs[0]:idxs[3]]
            stepview['act_g_in_del']     = self.act_delta[idxs[0]:idxs[1]]
            stepview['act_g_forget_del'] = self.act_delta[idxs[1]:idxs[2]]
            stepview['act_g_out_del']    = self.act_delta[idxs[2]:idxs[3]]
            stepview['act_in_xform_del'] = self.act_delta[idxs[3]:idxs[4]]

            self.fprop_views[step] = stepview

    def get_params(self):
        return [x.asnumpyarray()for x in self.params]

    def set_params(self, params):
        for param, set_param in zip(self.params, params):
            param[:] = set_param

    def set_hidden(self, state):
        self.fprop_views[0]['prev_h'] = state

    def fprop(self, X):

        self.cell_buffer[:] = 0

        self.X = X
        isz = self.input_size

        for step in range(self.seq_length):
            # slice input
            x = X[step * isz:(step+1) * isz]
            t = self.fprop_views[step]

            # compute gates (use act/gate as temporary buffers)
            self.backend.dot(self.W.T, x, t['gate_buf'])
            self.backend.dot(self.H.T, t['prev_h'], t['act_buf'])

            t['act_buf'][:]  = t['gate_buf'] + t['act_buf'] + self.b + self.v
            t['gate_buf'][:] = t['act_buf']

            # apply activations
            t['in_xform'][:] = self.activation(t['in_xform'])
            t['gates'][:]    = self.gate_activation(t['gates'])

            # compute cells
            t['c'][:] = t['g_in'] * t['in_xform'] + t['g_forget'] * t['prev_c']

            # compute hidden
            t['h'][:] = self.activation(t['c']) * t['g_out']

        return self.h_buffer

    def bprop(self, deltas):

        # intermediate deltas
        self.gate_act_delta[:] = 0
        self.cell_delta[:] = 0

        self.delta[:] = 0
        self.bias_delta_buf[:] = 0
        self.weight_delta_buf[:] = 0

        osz = self.output_size
        isz = self.input_size

        for step in reversed(range(self.seq_length)):

            # sliceA delta
            start = step * osz
            end   = start + osz
            prev_start = start - osz
            prev_end   = None if step == 0 else start  # For wrapping around

            in_delta      = deltas[start:end]
            prev_in_delta = deltas[prev_start:prev_end]

            # slice inputs
            x = self.X[step * isz: (step+1) * isz]
            t = self.fprop_views[step]

            # current cell delta
            t['act_g_out_del'][:] = in_delta * self.activation(t['c'])
            t['c_del'][:] += in_delta * t['g_out'] * self.activation_deriv(t['c'])

            # previous cell delta
            if step > 0:
                t['act_g_forget_del'][:] = t['c_del'] * t['prev_c']
                t['prev_c_del'][:] = t['c_del'] * t['g_forget']

            # remaining post-activation gate deltas (I think we can reuse
            # the post act delta buffer for the pre acts)
            t['act_g_in_del']     = t['c_del'] * t['in_xform']
            t['act_in_xform_del'] = t['c_del'] * t['g_in']

            # in transform delta (using in_transform as a temp buffer to store
            # derivatives. I think we want to avoid doing this in case multiple
            # layers need access)
            t['pre_in_xform'][:] = self.activation_deriv(t['pre_in_xform'])
            t['in_xform_del'][:] = t['pre_in_xform'] * t['act_in_xform_del']

            # gate delta
            t['pre_gates'][:] = self.gate_activation_deriv(t['pre_gates'])
            t['gates_del'][:] = t['pre_gates'] * t['act_gates_del']

            gdel = t['gate_del']
            # weight delta
            self.backend.dot(A=x, B=gdel.T, C=self.W_delta, beta=1.0)

            if step > 0:
                self.backend.dot(A=t['prev_h'], B=gdel.T, C=self.H_delta, beta=1.0)

            # accumulate bias deltas
            self.b_delta[:] += self.backend.sum(gdel, axis=1)
            self.v_delta[:] += self.backend.sum(gdel, axis=1)

            # deltas
            self.backend.dot(self.W, gdel, t['out_del'])
            self.backend.dot(self.H, gdel, t['h_del'])

            if step > 0:
                # changed this from out_delta to h_delta (bug in karp's code)
                prev_in_delta[:] += t['h_del']

        # normalize gradients by batch_size
        self.weight_delta_buf[:] /= self.batch_size
        self.bias_delta_buf[:] /= self.batch_size
        return self.delta
