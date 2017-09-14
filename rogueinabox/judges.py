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


class LoweringMeanSentence(Exception):
    """The mean is lower, this is bad!"""

class Judge(ABC):

    # TODO these should be configs
    death_sentence = False
    sample = 0
    save_score = False
    save_mean = False
    scores_file = "assets/scores.log"
    means_file = "assets/means.log"

    def __init__(self, agent):
        self.agent = agent
        self.rb = agent.rb
        self.scores = []
        self.means = []
        self.default_score = 0
        self.mean = 0
        self.highest_mean = 0
        self._reset_score()
        self.last_name = ""

    @abstractmethod
    def hook_before_action(self):
        """This should be called before the agent act."""
        pass

    @abstractmethod
    def hook_after_action(self):
        """This should be called after the agent act."""
        pass

    @abstractmethod
    def hook_game_over(self):
        """This should be called on game over."""
        pass

    def _register_score(self):
        self.scores.append(self.score)
        if len(self.scores)>self.sample:
            self.scores.pop(0)
        self._save_score()

    def _reset_score(self):
        self.score = self.default_score

    def _register_mean(self):
        if len(self.scores)>=self.sample:
            self.mean = float(sum(self.scores))/float(self.sample)
            self.means.append(self.mean)
            self._save_mean()

    def _save_score(self):
        if self.save_score:
            with open(self.scores_file, "a+") as file:
                file.write("{}\n".format(str(self.scores[-1])))

    def _save_mean(self):
        if self.save_mean:
            with open(self.means_file, "a+") as file:
                file.write("{}\n".format(str(self.mean)))

    def _save_weights(self):
        import datetime
        now = datetime.datetime.now().strftime("%Y%m%d-%H%M") 
        self.last_name = "assets/weights_{}_mean{}.h5".format(now, self.mean)
        self.agent.model.save_weights(self.last_name, overwrite=False)

    def _delete_old_weights(self):
        from os import remove, path
        if path.isfile(self.last_name):
            remove(self.last_name)


class SimpleExplorationJudge(Judge):
    
    death_sentence = False
    sample = 200
    stride = 10 
    save_score = True
    save_mean = True

    def hook_before_action(self):
        self.old_screen = self.rb.get_screen()
        self.old_level = self.rb._get_stat_from_screen("dungeon_level", self.old_screen)

    def hook_after_action(self):
        self.screen = self.rb.get_screen()
        self.level = self.rb._get_stat_from_screen("dungeon_level", self.screen)
        if self.level is None:
            # this will happen at game_over
            self.level = self.old_level
        if self.level > self.old_level:
            self.score += self.rb._count_passables_in_screen(self.old_screen)

    def hook_game_over(self):
        self.score += self.rb._count_passables_in_screen(self.old_screen)
        self._register_score()
        self._register_mean()
        if len(self.means) == 1 or (len(self.means) > 0 and len(self.means) % self.stride == 0):
            # will trigger when the first mean is recorded and then every self.stride games
            if self.mean > self.highest_mean:
                self.highest_mean = self.mean
                self._delete_old_weights()
                self._save_weights()
            #  elif self.death_sentence:
                #  raise LoweringMeanSentence("Last average score was higher than the current, this is bad!")
        self._reset_score()
