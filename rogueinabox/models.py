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

import numpy as np
from keras.models import Sequential, Model
from keras.layers import Dense, Flatten, initializers, Input, MaxPooling2D, Lambda
from keras.layers import Conv2D, ZeroPadding2D
from keras.layers.merge import concatenate
from keras.optimizers import Adam, RMSprop
from abc import ABC, abstractmethod

import skimage
from skimage import transform, exposure

class IncompatibleStateError(Exception):
    """To be raised if the state shape is not compatible with the model shape."""
    pass

#ABSTRACT CLASSES

#class naming:

#ModelReshapers
# Sl = Single layer
# Ml = Multi layer
# R = Reshape
# Nr = No reshape
# St = Stacking
# F = Flatten

#ModelBuilders
# A = Atari DeepMind model structure
# De = Dense model structure
# T = Three Towers model structure
# lT = Three Towers with line vision model structure

#ModelManagers
# nL = number of layers (e.g. 5L)

# each feature is separated by an underscore
# each classname is terminated by _ModelReshaper or _ModelBuilder
# example: Ml_R_F_ModelReshaper
# your ModelManager should inherit from both a ModelReshaper and a ModelBuilder

class ModelReshaper(ABC):
    def __init__(self, rogue_box, layers):
        """Initialize the ModelReshaper."""
        self.rb = rogue_box
        self.layers = layers
        self._set_shape()
        self._check_shape()

    @abstractmethod
    def _set_shape(self):
        """A tuple containing the state dimension must be assigned to self._shape in this method."""
        self._shape = (0, 0, 0)

    def _check_shape(self):
        """Check if the states provided in rogueinabox are compatible with this model."""
        state_generator = self.rb.state_generator
        if not self._shape == state_generator.shape:
            raise IncompatibleStateError()

    @abstractmethod
    def reshape_initial_state(self, first_frame):
        pass

    @abstractmethod
    def reshape_new_state(self, old_state, new_frame):
        pass

class ModelBuilder(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def build_model(self):
        """Build the model for Keras."""
        pass

class Sl_R_St_ModelReshaper(ModelReshaper):
    """Takes a single layer state, reshapes it and staks it layers
    times. Abstract class, needs a ModelBuilder"""

    def __init__(self, rogue_box, layers):
        #layers will be set to one anyway 
        super().__init__(rogue_box, 1)
        self.rows = 84
        self.columns = 84
        self.padding = False
        self.actions_num = len(rogue_box.get_actions())

    def _set_shape(self):
        self._shape = (1, 22, 80)

    def reshape_initial_state(self, first_frame):
        first_frame = skimage.transform.resize(first_frame, (84, 84))
        first_frame = skimage.exposure.rescale_intensity(first_frame, out_range=(0, 255))
        state = np.stack((first_frame for _ in range(self.layers)), axis=0)
        initial_agent_state = state.reshape(1, state.shape[0], state.shape[1], state.shape[2])
        return initial_agent_state

    def reshape_new_state(self, old_state, new_frame):
        new_frame = skimage.transform.resize(new_frame, (84, 84))
        new_frame = skimage.exposure.rescale_intensity(new_frame, out_range=(0, 255))
        new_frame = new_frame.reshape(1, 1, new_frame.shape[0], new_frame.shape[1])
        new_state = old_state[:, :-1, :, :]
        new_agent_state = np.append(new_frame, new_state, axis=1)
        return new_agent_state



class Ml_R_ModelReshaper(ModelReshaper):
    """Takes a multi layer state and reshapes it.
    Abstract class, needs a ModelBuilder"""

    def __init__(self, rogue_box, layers):
        super().__init__(rogue_box, layers)
        self.rows = 84
        self.columns = 84
        self.padding = False
        self.actions_num = len(rogue_box.get_actions())

    def _set_shape(self):
        self._shape = (self.layers, 22, 80)

    def reshape_initial_state(self, first_frame):
        first_frame = skimage.transform.resize(first_frame, (self.layers, 84, 84))
        initial_agent_state = first_frame.reshape(1, first_frame.shape[0], first_frame.shape[1], first_frame.shape[2])
        return initial_agent_state

    def reshape_new_state(self, old_state, new_frame):
        new_frame = skimage.transform.resize(new_frame, (self.layers, 84, 84))
        new_agent_state = new_frame.reshape(1, new_frame.shape[0], new_frame.shape[1], new_frame.shape[2])
        return new_agent_state

class Ml_F_ModelReshaper(ModelReshaper):
    """Takes a multi layer state flattens it.
    Abstract class, needs a ModelBuilder"""

    def __init__(self, rogue_box, layers):
        super().__init__(rogue_box, layers)
        self.flat_dim = self.layers * 22 * 80
        self.padding = False
        self.actions_num = len(rogue_box.get_actions())

    def _set_shape(self):
        self._shape = (self.layers, 22, 80)

    def reshape_initial_state(self, first_frame):
        # the frame should have shape 3x22x80
        initial_agent_state = first_frame.reshape(1, self.flat_dim)
        return initial_agent_state

    def reshape_new_state(self, old_state, new_frame):
        new_agent_state = new_frame.reshape(1, self.flat_dim)
        return new_agent_state

class Ml_Nr_ModelReshaper(ModelReshaper):
    """Takes a multi layer state without reshaping it.
    Abstract class, needs a ModelBuilder"""

    def __init__(self, rogue_box, layers):
        super().__init__(rogue_box, layers)
        self.rows = 22
        self.columns = 80
        self.padding = True
        self.actions_num = len(rogue_box.get_actions())

    def _set_shape(self):
        self._shape = (self.layers, 22, 80)

    def reshape_initial_state(self, first_frame):
        initial_agent_state = first_frame.reshape(1, first_frame.shape[0], first_frame.shape[1], first_frame.shape[2])
        return initial_agent_state

    def reshape_new_state(self, old_state, new_frame):
        new_agent_state = new_frame.reshape(1, new_frame.shape[0], new_frame.shape[1], new_frame.shape[2])
        return new_agent_state

class Dummy_ModelReshaper(ModelReshaper):
    """Use only to build random unmodified history, never use the in actual training"""

    def __init__(self, rogue_box, layers = 1):
        # layers set to one, but it isnt used anyway in the dummy model
        super().__init__(rogue_box, 1)
        self.actions_num = len(rogue_box.get_actions())

    def _set_shape(self):
        self._shape = (22, 80)

    def reshape_initial_state(self, first_frame):
        return first_frame

    def reshape_new_state(self, old_state, new_frame):
        return new_frame

class A_Model(ModelBuilder):
    """ Builds a model similar to the one used by DeepMind for Atari games.
    Abstract class, needs a ModelReshaper"""
    def __init__(self):
        super().__init__()

    def build_model(self):
        initializer = initializers.random_normal(stddev=0.02)
        model = Sequential()
        if self.padding:
            model.add(ZeroPadding2D(padding=(1, 0), data_format="channels_first", input_shape=(self.layers, self.rows, self.columns)))
        model.add(Conv2D(32, (8, 8), activation="relu", data_format="channels_first",
                         strides=(4, 4), kernel_initializer=initializer, padding='same',
                         input_shape=(self.layers, self.rows, self.columns)))
        model.add(Conv2D(64, (4, 4), activation="relu", data_format="channels_first", strides=(2, 2),
                         kernel_initializer=initializer, padding='same'))
        model.add(Conv2D(64, (3, 3), activation="relu", data_format="channels_first", strides=(1, 1),
                         kernel_initializer=initializer, padding='same'))
        model.add(Flatten())
        model.add(Dense(512, activation="relu", kernel_initializer=initializer))
        model.add(Dense(self.actions_num, kernel_initializer=initializer))

        adam = Adam(lr=1e-6)
        model.compile(loss='mse', optimizer=adam)
        return model

class De_Model(ModelBuilder):
    """ Builds a model with consecutive dense layers.
    Use only with a flat ModelReshaper.
    Abstract class, needs a ModelReshaper"""
    def __init__(self):
        super().__init__()

    def build_model(self):
        model = Sequential()
        model.add(Dense(2048, input_dim=self.flat_dim, activation="relu", kernel_initializer="random_normal"))
        model.add(Dense(1024, activation="relu", kernel_initializer="random_normal"))
        model.add(Dense(512, activation="relu", kernel_initializer="random_normal"))
        model.add(Dense(self.actions_num, activation="relu", kernel_initializer="random_normal"))

        adam = Adam(lr=1e-6)
        model.compile(loss='mse', optimizer=adam)
        return model

class T_ModelBuilder(ModelBuilder):
    """ Builds a model with three towers, each one with a focus on different
    parts of the state.
    Abstract class, needs a ModelReshaper"""

    def __init__(self):
        super().__init__()
        self.depth = 2

    def build_model(self):
    
        initializer = initializers.random_normal(stddev=0.02)
    
        input_img = Input(shape=(self.layers, 22, 80))
        input_2 = Lambda(lambda x: x[:, 1:, :, :], output_shape=lambda x: (None, self.layers - 1, 22, 80))(input_img) # no map channel
    
        # whole map
        tower_1 = Conv2D(64, (3, 3), data_format="channels_first", strides=(1, 1), kernel_initializer=initializer, padding="same")(input_img)
        tower_1 = Conv2D(32, (3, 3), data_format="channels_first", strides=(1, 1), kernel_initializer=initializer, padding="same")(tower_1)
        tower_1 = MaxPooling2D(pool_size=(22, 80), data_format="channels_first")(tower_1)
    
    
        #tower2
        tower_2 = MaxPooling2D(pool_size=(2, 2), data_format="channels_first")(input_2)
        for _ in range(self.depth):
            tower_2 = Conv2D(32, (3, 3), data_format="channels_first", strides=(1, 1), kernel_initializer=initializer, padding="same", activation='relu')(tower_2)
        tower_2 = MaxPooling2D(pool_size=(11, 40), data_format="channels_first")(tower_2)
    
        #tower3
        tower_3 = MaxPooling2D(pool_size=(3, 6), data_format="channels_first", padding='same')(input_2)
        for _ in range(self.depth):
            tower_3 = Conv2D(32, (3, 3), data_format="channels_first", strides=(1, 1), kernel_initializer=initializer, padding="same", activation='relu')(tower_3)
        tower_3 = MaxPooling2D(pool_size=(8, 14), data_format="channels_first", padding='same')(tower_3)
    
        merged_layers = concatenate([tower_1, tower_2, tower_3], axis=1)
    
        flat_layer = Flatten()(merged_layers)
        
        predictions = Dense(5, kernel_initializer=initializer)(flat_layer)
        model = Model(inputs=input_img, outputs=predictions)
        
        rmsprop = RMSprop(lr=0.00025)
        model.compile(loss='mse', optimizer=rmsprop)
        return model

class lT_ModelBuilder(ModelBuilder):
    """ Builds a model with three towers, each one with a different vision of
    the map.
    Abstract class, needs a ModelReshaper"""
    def __init__(self):
        super().__init__()

    def build_model(self):
    
        initializer = initializers.random_normal(stddev=0.02)
    
        input_img = Input(shape=(self.layers, 22, 80))
        input_2 = Lambda(lambda x: x[:, :2, :, :], output_shape=lambda x: (None, 2, 22, 80))(input_img) # no map channel
    
        # whole map 10x1
        tower_1 = ZeroPadding2D(padding=(1, 0), data_format="channels_first")(input_2)
        tower_1 = Conv2D(32, (10, 1), data_format="channels_first", strides=(7, 1), kernel_initializer=initializer, padding="valid")(tower_1)
        tower_1 = Flatten()(tower_1)
    
        # whole map 1x10
        tower_2 = Conv2D(32, (1, 10), data_format="channels_first", strides=(1, 7), kernel_initializer=initializer, padding="valid")(input_2)
        tower_2 = Flatten()(tower_2)
    
        # whole map 3x3 then maxpool 22x80
        tower_3 = Conv2D(32, (3, 3), data_format="channels_first", strides=(1, 1), kernel_initializer=initializer, padding="same")(input_2)
        tower_3 = MaxPooling2D(pool_size=(22, 80), data_format="channels_first")(tower_3)
        tower_3 = Flatten()(tower_3)
    
        merged_layers = concatenate([tower_1, tower_2, tower_3], axis=1)
    
        predictions = Dense(4, kernel_initializer=initializer)(merged_layers)
        model = Model(inputs=input_img, outputs=predictions)
        
        adam = Adam(lr=1e-6)
        model.compile(loss='mse', optimizer=adam)
        return model

class Dummy_ModelBuilder(ModelBuilder):
    """Use only to build random unmodified history, dont call the model"""
    def __init__(self):
        super().__init__()

    def build_model(self):
        """should never be called for this model manager"""
        model = Sequential()
        model.add(Dense(self.actions_num, input_shape=(80,)))
        adam = Adam(lr=1e-6)
        model.compile(loss='mse', optimizer=adam)
        return model

#CLASSES

class T_3L_Ml_Nr_ModelManager(Ml_Nr_ModelReshaper, T_ModelBuilder):
    def __init__(self, rogue_box):
        layers = 3
        Ml_Nr_ModelReshaper.__init__(self, rogue_box, layers)
        T_ModelBuilder.__init__(self)

class T_4L_Ml_Nr_ModelManager(Ml_Nr_ModelReshaper, T_ModelBuilder):
    def __init__(self, rogue_box):
        layers = 4
        Ml_Nr_ModelReshaper.__init__(self, rogue_box, layers)
        T_ModelBuilder.__init__(self)

class T_5L_Ml_Nr_ModelManager(Ml_Nr_ModelReshaper, T_ModelBuilder):
    def __init__(self, rogue_box):
        layers = 5
        Ml_Nr_ModelReshaper.__init__(self, rogue_box, layers)
        T_ModelBuilder.__init__(self)

class Dummy_ModelManager(Dummy_ModelReshaper, Dummy_ModelBuilder):
    def __init__(self, rogue_box):
        Dummy_ModelReshaper.__init__(self, rogue_box)
        Dummy_ModelBuilder.__init__(self)
