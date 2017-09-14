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

from abc import ABC, abstractmethod

import pickle
import random
import numpy as np

import os
from collections import deque


class HistoryManager(ABC):
    """A class responsible for saving history and loading batch of it for training purposes."""

    def __init__(self, agent):
        """Constructor for History"""
        self.agent = agent
        self._history = None

    @property
    def history(self):
        """Return the history"""
        return self._history

    def hist_len(self):
        """Return the history length"""
        return len(self._history)

    def save_history_on_file(self, filename):
        """Save the history on file"""
        print("Saving history...")
        with open(filename, "wb") as history:
            pickle.dump(self._history, history)
            print("History saved!")

    def load_history_from_file(self, filename):
        """Load the history from the filesystem"""
        if os.path.isfile(filename):
            print("History found, loading...")
            with open(filename, "rb") as history:
                self._history = pickle.load(history)
                print("History loaded!")

    @abstractmethod
    def update_history(self):
        """Method responsible for saving the new state into the history"""
        pass

    @abstractmethod
    def pick_batch(self):
        """Method responsible for picking a batch of states from the history to train"""
        pass


class FIFORandomPickHM(HistoryManager):
    """Simple fifo queue history implementation"""

    def __init__(self, agent):
        super().__init__(agent)
        self._history = deque()

    def update_history(self, action_index, reward, terminal):
        """Update the fifo history queue
        return True if an item was added, False otherwise
        """
        self._history.appendleft((self.agent.old_state, action_index, reward, self.agent.state, terminal))
        if len(self._history) > self.agent.parameters["histsize"]:
            self._history.pop()
        return True

    def pick_batch(self, batch_dimension):
        return random.sample(list(self._history), batch_dimension)

class NearDoorRandomPickHM(HistoryManager):
    """A more balanced history implementation for ExitRoom"""

    def __init__(self, agent):
        super().__init__(agent)
        self._history = deque()

    def _distance_from_door(self, state):
        # warning: the rogue may cover the door
        rogue_pos = np.argwhere(state[1] == 255)
        if rogue_pos.shape[0] == 0: return 1000
        rx,ry = rogue_pos[0][0],rogue_pos[0][1]
        doors = np.argwhere(state[2] == 255)
        dl = []
        for dpos in doors:
            dx,dy = dpos[0],dpos[1]
            dl.append(abs(dx-rx)+abs(dy-ry))
        if dl == []: return 1000
        mind = min(dl)
        print("distance = %", mind)
        return mind

    def update_history(self, action_index, reward, terminal):
        """Update the balanced history queue
        return True if an item was added, False otherwise
        """
        item_added = False
        if (reward > 0) or (random.random() < self._distance_from_door(self.agent.state[0])**-2.):  
            self._history.appendleft((self.agent.old_state, action_index, reward, self.agent.state, terminal))
            item_added = True
        if len(self._history) > self.agent.parameters["histsize"]:
            self._history.pop()
        return item_added

    def pick_batch(self, batch_dimension):
        return random.sample(list(self._history), batch_dimension)

class StatisticBalanceRandomPickHM(HistoryManager):
    """Simple balanced history implementation"""

    def __init__(self, agent):
        super().__init__(agent)
        self._history = deque()

    def update_history(self, action_index, reward, terminal):
        """Update the balanced history queue
        return True if an item was added, False otherwise
        """
        item_added = False
        if (reward >= 0) or (self.agent.parameters["iteration"] % 7 == 0):
            self._history.appendleft((self.agent.old_state, action_index, reward, self.agent.state, terminal))
            item_added = True
        if len(self._history) > self.agent.parameters["histsize"]:
            self._history.pop()
        return item_added

    def pick_batch(self, batch_dimension):
        return random.sample(list(self._history), batch_dimension)


class StatisticBalance2RandomPickHM(HistoryManager):
    """Simple balanced history implementation"""

    def __init__(self, agent):
        super().__init__(agent)
        self._history = deque()

    def update_history(self, action_index, reward, terminal):
        """Update the balanced history queue
        return True if an item was added, False otherwise
        """
        item_added = False
        if reward > 0 or (reward < 0 and random.random() < 0.2):
            self._history.appendleft((self.agent.old_state, action_index, reward, self.agent.state, terminal))
            item_added = True
        if len(self._history) > self.agent.parameters["histsize"]:
            self._history.pop()
        return item_added

    def pick_batch(self, batch_dimension):
        return random.sample(list(self._history), batch_dimension)
