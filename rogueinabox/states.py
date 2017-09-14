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
import scipy
import itertools
from abc import ABC, abstractmethod

#class naming:
# M = Map
# P = Player
# S = Stairs
# D = Doors
# H = Heatmap
# Sn = Snake
# each layer is separated by an underscore
# each classname is terminated by _StateGenerator
# example: M_P_SD_H_StateGenerator

# ABSTRACT CLASSES

class StateGenerator(ABC):

    def __init__(self, rogue_box):
        self.rb = rogue_box
        self._set_shape()
        self.need_reset = False

    @abstractmethod
    def _set_shape(self):
        """The implementing class MUST set the state _shape (should be a tuple)."""
        self._shape = (0, 0, 0)

    @property
    def shape(self):
        """Should return the state shape this generator uses, in a form of a tuple."""
        return self._shape

    @abstractmethod
    def compute_state(self):
        """Should compute the state and return it."""
        pass

    def parse_screen(self):
        positions = {}
        positions["stairs_pos"] = [self.rb.stairs_pos]
        positions["player_pos"] = [self.rb.player_pos]
        positions["passable_pos"] = []
        positions["doors_pos"] = []
        for i, j in itertools.product(range(1, 23), range(80)):
            pixel = self.rb.screen[i][j]
            if pixel not in '|- ':
                positions["passable_pos"].append((i, j))
            if pixel == '+':
                positions["doors_pos"].append((i, j))
        return positions
    
    def set_layer(self, state, layer, positions, value):
        for pos in positions:
            if pos:
                i, j = pos
                state[layer][i - 1][j] = value
        return state
    
    def game_over_state(self, layers):
        # the screen is the tombstone game over screen
        # return an array of 0 to differentiate
        return np.zeros([layers, 22, 80], dtype=np.uint8)
    
    def unknown_state(self, layers):
        # the screen is inventory, option or a transition screen
        # return an array of 1 to differentiate
        # the agents should not get to this case
        return np.zeros([layers, 22, 80], dtype=np.uint8)

class H_StateGenerator(StateGenerator):
    '''abstract class, needs compute_state to instantiate'''
    def __init__(self, rogue_box):
        super().__init__(rogue_box)
        self.heatmap = np.zeros((22, 80), dtype=np.uint8)
        self.first_state = True

    def find_player(self, screen):
        player_pos = None
        for i, j in itertools.product(range(1, 23), range(80)):
            pixel = screen[i][j]
            if pixel == '@':
                player_pos = (i-1, j)
        return player_pos
    
    def find_passable(self, screen):
        passable_pos = []
        for i, j in itertools.product(range(1, 23), range(80)):
            pixel = screen[i][j]
            if pixel not in '|- ':
                passable_pos.append((i-1, j))
        return passable_pos
    
    def find_adjacent(self, player_pos):
        if not player_pos:
            return []
        adjacent_pos = [(max(0, player_pos[0]-1), player_pos[1]), (player_pos[0], max(0, player_pos[1]-1)), (min(21, player_pos[0]+1), player_pos[1]), (player_pos[0], min(79, player_pos[1]+1))]
        return adjacent_pos
    
    def find_adjacent_passable(self, screen, player_pos):
        passable_pos = self.find_passable(screen)
        adjacent_pos = self.find_adjacent(player_pos)
        return [pos for pos in adjacent_pos if pos in passable_pos]
    
    def update_heatmap(self, screen, heatmap):
        player_pos = self.find_player(screen)
        if not player_pos:
            return heatmap
        adjacent_passable = self.find_adjacent_passable(screen, player_pos)
        update = min([heatmap[i][j] for i, j in adjacent_passable])
        heatmap[player_pos[0]][player_pos[1]] = update + 1
        return heatmap

    def handle_first_state_heatmap(self):
        player_pos = self.find_player(self.rb.screen)
        if not player_pos:
            pass
        else:
            self.heatmap[player_pos[0]][player_pos[1]] = 1
        self.first_state = False

    def set_heatmap_layer(self, state, layer, layers):
        if self.first_state:
            self.handle_first_state_heatmap()
        else:
            self.heatmap = self.update_heatmap(self.rb.screen, self.heatmap)
        state[layer] = np.copy(self.heatmap)
        if 3 in state[layer]:
            self.need_reset = True
            state = np.zeros([layers, 22, 80], dtype=np.uint8)
            self.heatmap = np.zeros((22, 80), dtype=np.uint8)
            self.first_state = True
        else:
            state[layer][state[layer] == 1] == 127
            state[layer][state[layer] == 2] == 255
        return state

class Sn_StateGenerator(StateGenerator):
    '''abstract class, needs compute_state to instantiate'''
    def set_snake_layer(self, state, layer):
        unit = 255/10
        past_positions = self.rb.past_positions
        for i, pos in enumerate(past_positions):
            state[layer][pos[0]-1][pos[1]] = (i+1)*unit
        return state


#SUBCLASSES

class StringListStateGenerator(StateGenerator):
    """returns a list of strings and not a numpy array"""

    def _set_shape(self):
        self._shape = (22, 80)

    def compute_state(self):
        return self.rb.screen[1:23]

class AsciiToIntStateGenerator(StateGenerator):
    def __init__(self, rogue_box):
        super().__init__(rogue_box)
        self.ascii_to_int_map = self._init_numeric_map()

    @staticmethod
    def _init_numeric_map():
        """initialize ascii_to_int_map"""
        monsters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        environment = "|+%#.-^ "
        items = "!*)]:?$=/"
        rogue = "@"
        count = 0
        ascii_to_int_map = {}
        for char in monsters + environment + items + rogue:
            ascii_to_int_map[char] = count
            count += 1
        return ascii_to_int_map

    def compute_state(self):
        """return a 22x80 numpy array filled with a numeric state"""
        if self.rb.is_map_view(self.rb.screen):
            # the screen is a map of the dungeon
            # parse it and return a numerical representation
            state = np.zeros([1, 22, 80], dtype=np.uint8)
            for i, j in itertools.product(range(1, 23), range(80)):
                key = self.rb.screen[i][j]
                state[0][i - 1][j] = self.ascii_to_int_map[key]
        elif self.rb.game_over():
            self.game_over_state(1)
        else:
            self.unknown_state(1)
        return state


class M_P_S_StateGenerator(StateGenerator):
    def __init__(self, rogue_box):
        super().__init__(rogue_box)

    def _set_shape(self):
        self._shape = (3, 22, 80)

    def compute_state(self):
        if self.rb.is_map_view(self.rb.screen):
            state = np.zeros([3, 22, 80], dtype=np.uint8)
            positions = self.parse_screen()

            # layer 0: the map
            state = self.set_layer(state, 0, positions["passable_pos"], 255)

            # layer 1: the player position
            state = self.set_layer(state, 1, positions["player_pos"], 255)

            # layer 2: the stairsposition
            state = self.set_layer(state, 2, positions["stairs_pos"], 255)

        elif self.rb.game_over():
            state = self.game_over_state(3)
        else:
            state = self.unknown_state(3)
        return state


class M_P_D_StateGenerator(StateGenerator):

    def _set_shape(self):
        self._shape = (3, 22, 80)

    def compute_state(self):
        """return a 3x22x80 numpy array filled with a numeric state"""
        if self.rb.is_map_view(self.rb.screen):
            state = np.zeros([3, 22, 80], dtype=np.uint8)
            positions = self.parse_screen()

            # layer 0: the map
            state = self.set_layer(state, 0, positions["passable_pos"], 255)

            # layer 1: the player position
            state = self.set_layer(state, 1, positions["player_pos"], 255)

            # layer 2: the doors positions
            state = self.set_layer(state, 2, positions["doors_pos"], 255)

        elif self.rb.game_over():
            state = self.game_over_state(3)
        else:
            state = self.unknown_state(3)
        return state

class M_P_DS_StateGenerator(StateGenerator):

    def _set_shape(self):
        self._shape = (3, 22, 80)

    def compute_state(self):
        """return a 3x22x80 numpy array filled with a numeric state"""
        if self.rb.is_map_view(self.rb.screen):
            state = np.zeros([3, 22, 80], dtype=np.uint8)
            positions = self.parse_screen()

            # layer 0: the map
            state = self.set_layer(state, 0, positions["passable_pos"], 255)

            # layer 1: the player position
            state = self.set_layer(state, 1, positions["player_pos"], 255)

            # layer 2: doors and stairs positions
            state = self.set_layer(state, 2, positions["doors_pos"], 255)
            state = self.set_layer(state, 2, positions["stairs_pos"], 255)

        elif self.rb.game_over():
            state = self.game_over_state(3)
        else:
            state = self.unknown_state(3)
        return state

class M_P_D_H_StateGenerator(H_StateGenerator):
    def _set_shape(self):
        self._shape = (4, 22, 80)

    def compute_state(self):
        """return a 4x22x80 numpy array filled with a numeric state"""
        if self.rb.is_map_view(self.rb.screen):
            state = np.zeros([4, 22, 80], dtype=np.uint8)
            positions = self.parse_screen()

            # layer 0: the map
            state = self.set_layer(state, 0, positions["passable_pos"], 255)

            # layer 1: the player position
            state = self.set_layer(state, 1, positions["player_pos"], 255)

            # layer 2: the doors positions
            state = self.set_layer(state, 2, positions["doors_pos"], 255)
            
            # layer 3: heatmap of past positions
            state = self.set_heatmap_layer(state, 3, 4)

        elif self.rb.game_over():
            state = self.game_over_state(4)
            self.heatmap = np.zeros((22, 80), dtype=np.uint8)
            self.first_state = True
        else:
            state = self.unknown_state(4)
        return state
    
class M_P_DS_H_StateGenerator(H_StateGenerator):
    def _set_shape(self):
        self._shape = (4, 22, 80)

    def compute_state(self):
        """return a 4x22x80 numpy array filled with a numeric state"""
        if self.rb.is_map_view(self.rb.screen):
            state = np.zeros([4, 22, 80], dtype=np.uint8)
            positions = self.parse_screen()

            # layer 0: the map
            state = self.set_layer(state, 0, positions["passable_pos"], 255)

            # layer 1: the player position
            state = self.set_layer(state, 1, positions["player_pos"], 255)

            # layer 2: the doors and stairs positions
            state = self.set_layer(state, 2, positions["doors_pos"], 255)
            state = self.set_layer(state, 2, positions["stairs_pos"], 255)
            
            # layer 3: heatmap of past positions
            state = self.set_heatmap_layer(state, 3, 4)
            
        elif self.rb.game_over():
            state = self.game_over_state(4)
            self.heatmap = np.zeros((22, 80), dtype=np.uint8)
            self.first_state = True
        else:
            state = self.unknown_state(4)
        return state

class M_P_D_Sn_StateGenerator(Sn_StateGenerator):

    def _set_shape(self):
        self._shape = (4, 22, 80)

    def compute_state(self):
        """return a 3x22x80 numpy array filled with a numeric state"""
        if self.rb.is_map_view(self.rb.screen):
            state = np.zeros([4, 22, 80], dtype=np.uint8)
            positions = self.parse_screen()

            # layer 0: the map
            state = self.set_layer(state, 0, positions["passable_pos"], 255)

            # layer 1: the player position
            state = self.set_layer(state, 1, positions["player_pos"], 255)

            # layer 2: the doors and stairs positions
            state = self.set_layer(state, 2, positions["doors_pos"], 255)

            # layer 3: snake-like of past positions, with fading
            state = self.set_snake_layer(state, 3)

        elif self.rb.game_over():
            state = self.game_over_state(4)
        else:
            state = self.unknown_state(4)
        return state

class M_P_DS_Sn_StateGenerator(Sn_StateGenerator):

    def _set_shape(self):
        self._shape = (4, 22, 80)

    def compute_state(self):
        """return a 3x22x80 numpy array filled with a numeric state"""
        if self.rb.is_map_view(self.rb.screen):
            state = np.zeros([4, 22, 80], dtype=np.uint8)
            positions = self.parse_screen()

            # layer 0: the map
            state = self.set_layer(state, 0, positions["passable_pos"], 255)

            # layer 1: the player position
            state = self.set_layer(state, 1, positions["player_pos"], 255)

            # layer 2: the doors and stairs positions
            state = self.set_layer(state, 2, positions["doors_pos"], 255)
            state = self.set_layer(state, 2, positions["stairs_pos"], 255)

            # layer 3: snake-like of past positions, with fading
            state = self.set_snake_layer(state, 3)

        elif self.rb.game_over():
            state = self.game_over_state(4)
        else:
            state = self.unknown_state(4)
        return state

class M_P_D_S_Sn_StateGenerator(Sn_StateGenerator):

    def _set_shape(self):
        self._shape = (5, 22, 80)

    def compute_state(self):
        """return a 3x22x80 numpy array filled with a numeric state"""
        if self.rb.is_map_view(self.rb.screen):
            state = np.zeros([5, 22, 80], dtype=np.uint8)
            positions = self.parse_screen()

            # layer 0: the map
            state = self.set_layer(state, 0, positions["passable_pos"], 255)

            # layer 1: the player position
            state = self.set_layer(state, 1, positions["player_pos"], 255)

            # layer 2: the doors positions
            state = self.set_layer(state, 2, positions["doors_pos"], 255)
                
            # layer 3: the stairs positions
            state = self.set_layer(state, 3, positions["stairs_pos"], 255)

            # layer 4: snake-like of past positions, with fading
            state = self.set_snake_layer(state, 4)

        elif self.rb.game_over():
            state = self.game_over_state(5)
        else:
            state = self.unknown_state(5)
        return state
