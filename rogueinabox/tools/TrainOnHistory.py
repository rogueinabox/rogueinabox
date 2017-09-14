#!/usr/bin/env python
# coding: utf-8

#Copyright (C) 2017 Andrea Asperti, Carlo De Pieri, Gianmaria Pedrini
#
#This file is part of Rogueinabox.
#
#Rogueinabox is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#Rogueinabox is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

import pickle
import numpy as np

from keras.models import Sequential, Model
from keras.layers import Dense, Flatten, initializers, Input, MaxPooling2D, Lambda
from keras.layers import Conv2D, ZeroPadding2D
from keras.layers.merge import concatenate
from keras.optimizers import Adam

def build_model():
    # insert here the model you want to use
    pass

model = build_model()

from keras.utils import plot_model
plot_model(model, to_file='model.png', show_shapes=True)

print("loading history...")
h = pickle.load(open('history.pkl', 'rb'))
print("history loaded!")

def setup_epoch():
    inputs = np.zeros((len(h), 4, 22, 80))
    targets = np.zeros((len(h), 4))

    for i in range(len(h)):
        old_state = h[i][0]
        action_index = h[i][1]
        reward = h[i][2]
        new_state = h[i][3]
        terminal = h[i][4]
    
        inputs[i] = old_state
        targets[i] = model.predict(old_state)

        if terminal:
            targets[i, action_index] = reward
        else:
            Q_new_state = model.predict(new_state)
            targets[i, action_index] = reward + 0.99 * np.max(Q_new_state)
    return (inputs, targets)

#uncomment if you want to restart from saved weights
#model.load_weights("weights.h5")
iteration = 0
while True:
    iteration += 1
    print(iteration)
    inputs, targets = setup_epoch()
    model.fit(inputs, targets, epochs = 100, batch_size=32)
    model.save_weights("weights.h5", overwrite=True)
