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

import csv
import random

import matplotlib.pyplot as plt
import numpy as np
import os
from abc import ABC, abstractmethod

from logger import Logger, Log
from rogueinabox import RogueBox
from stalkomatic import StalkOMatic
from ui.UIManager import UIManager

# Log levels
LOG_LEVEL_NONE = 0
LOG_LEVEL_SOME = 1
LOG_LEVEL_MORE = 2
LOG_LEVEL_ALL = 3

# ABSTRACT CLASSES

class Agent(ABC):

    def __init__(self, configs):
        pass

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def act(self):
        pass

class LearnerAgent(Agent):

    @abstractmethod
    def observe(self):
        pass
    
    @abstractmethod
    def predict(self):
        pass

    @abstractmethod
    def train(self):
        pass

# AGENTS

class UserAgent(Agent):
    def __init__(self, configs):
        self.c = configs
        #init roguebox
        self.rb = RogueBox(configs)
        self.ui = UIManager.init(self.c["userinterface"], self.rb)
        self.l = Logger(log_depth=self.c["verbose"], log_targets=["file", "ui"], ui=self.ui)
        self.ui.on_key_press(self._act_callback)

    def run(self):
        self.ui.start_ui()

    def act(self, action):
        return self.rb.send_command(action)

    def _act_callback(self, event):
        action = event.char
        logs = [Log("action_time", "Action ({}) time".format(action), LOG_LEVEL_MORE, mean=10)]
        self.l.start_log_timer(logs)
        reward, _, __ = self.act(action)
        self.l.stop_log_timer(logs)
        logs = [
            Log("action_state", "My previous state: \n {}".format(self.ui.read_rogue()), LOG_LEVEL_ALL),
            Log("chosen_action", "My chosen action: {} got reward: {}".format(action, reward), LOG_LEVEL_MORE),
        ]
        self.l.log(logs)
        self.ui.draw_from_rogue()
        if not self.rb.is_running():
            exit()

class RandomAgent(Agent):
    def __init__(self, configs):
        self.rb = RogueBox(configs)
        self._pending_action_timer = None
        self.ui = UIManager.init(configs["userinterface"], self.rb)
        self.l = Logger(log_depth=configs["verbose"], log_targets=["file", "ui"], ui=self.ui)
        self.ui.on_key_press(self._keypress_callback)
        self._timer_value = 100
        self._pending_action_timer = self.ui.on_timer_end(self._timer_value, self._act_callback)

    def run(self):
        self.ui.start_ui()

    def act(self):
        actions = self.rb.get_actions()
        action = random.choice(actions)
        logs = [Log("random_action_time", "Action ({}) time".format(action), LOG_LEVEL_MORE, mean=10)]
        self.l.start_log_timer(logs)
        reward, _, __ = self.rb.send_command(action)
        self.l.stop_log_timer(logs)
        logs = [
            Log("action_state", "My previous state: \n {}".format(self.ui.read_rogue()), LOG_LEVEL_ALL),
            Log("chosen_action", "My chosen action: {} got reward: {}".format(action, reward), LOG_LEVEL_MORE),
        ]
        self.l.log(logs)
        return reward

    def _keypress_callback(self, event):
        if event.char == 'q' or event.char == 'Q':
            self.rb.quit_the_game()
            exit()
        elif event.char == 'r' or event.char == 'R':
            # we need to stop the agent from acting
            # or it will try to write to a closed pipe
            self.ui.cancel_timer(self._pending_action_timer)
            self.rb.reset()
            self._pending_action_timer = self.ui.on_timer_end(self._timer_value, self._act_callback)

    def _act_callback(self):
        reward = self.act()
        self.ui.draw_from_rogue()
        if not self.rb.game_over():
            # renew the callback
            self._pending_action_timer = self.ui.on_timer_end(self._timer_value, self._act_callback)
        else:
            self.ui.cancel_timer(self._pending_action_timer)

class StalkerAgent(Agent):
    """A reinforced Q-learning agent. It will use the rogomatic tool to build an initial history and then train on
    it."""

    def __init__(self, configs):
        import history, models
        
        # class instances
        self.rogomatic = StalkOMatic(configs)
        self.model_manager = getattr(models, configs["model_manager"])(self.rogomatic)
        self.history_manager = getattr(history, configs["history_manager"])(self)
        # configs
        self.configs = configs
        self.configs["iteration"] = 1
        self.configs["actions"] = self.rogomatic.get_actions()
        self.configs["actions_num"] = len(self.configs["actions"])
        # gui stuff
        ui = None
        log_targets = []
        if configs["logsonfile"]:
            log_targets.append("file")
        if self.configs["gui"]:
            self.ui = UIManager.init(configs["userinterface"], self.rogomatic)
            self._pending_action = None
            ui = self.ui
            log_targets.append("ui")
            self.l = Logger(log_depth=configs["verbose"], log_targets=log_targets, ui=ui)
        else:
            log_targets.append("terminal")
            self.l = Logger(log_depth=configs["verbose"], log_targets=log_targets)
        # state
        self.state = self.model_manager.reshape_initial_state(self.rogomatic.compute_state())
        self.old_state = self.state
        self.last_pos = self.rogomatic.player_pos
        self.same_pos_count = 0
        self.starting = False

    def run(self):
        self.build_history()

    def is_freezed(self):
        new_pos = self.rogomatic.player_pos
        if new_pos == self.last_pos:
            self.same_pos_count += 1
        else:
            self.last_pos = new_pos
            self.same_pos_count = 0
        if self.same_pos_count > 1000:
            self.same_pos_count = 0
            return True
        else:
            return False
            
    def _build_callback(self):
        self._build_step()
        self.ui.draw_from_rogue()
        self._pending_action = self.ui.on_timer_end(self.configs["gui_delay"], lambda: self._build_callback())

    def _build_key_callback(self, event):
        if event.char == 'q' or event.char == 'Q':
            history_log = [Log("history_done", "Building history: done!", 2)]
            self.history_manager.save_history_on_file("assets/rogomatic_history.pkl")
            self.l.log(history_log)
            self.rogomatic.send_command('Q')
            self.rogomatic.quit_the_game()
            exit()

    def build_history(self):
        if self.configs["gui"]:
            self._pending_action = self.ui.on_timer_end(100, lambda: self._build_callback())
            self.ui.on_key_press(self._build_key_callback)
            self.ui.start_ui()
        else:
            while self.history_manager.hist_len() < self.configs["histsize"]:
                self._build_step()
            history_log = [Log("history_done", "Building history: done!", 2)]
            self.history_manager.save_history_on_file("assets/rogomatic_history.pkl")
            self.l.log(history_log)
            self.rogomatic.send_command('Q')

    def _build_step(self):
            # always provide an initial state
            if self.history_manager.hist_len() % 100 == 0:
                hlen = [Log("history_len", "Current history lenght is: {}".format(self.history_manager.hist_len()), 2)]
                self.l.log(hlen)
            if self.starting:
                self.starting = False
                state = self.rogomatic.compute_state()
                self.state = self.model_manager.reshape_initial_state(state)
            self.old_state = self.state
            # make rogomatic perform its action
            if random.random() > 0.5:
                actions = self.rogomatic.get_actions()
                action = random.choice(actions)
            else:
                action = '\n'
            reward, new_state, terminal = self.rogomatic.send_command(action)
            # reshape the state
            self.state = self.model_manager.reshape_new_state(self.old_state, new_state)
            # parse the screen, finding out the performed action
            new_statusbar = self.rogomatic.screen[-1]
            parsed_command = self.rogomatic.parse_command_re.match(new_statusbar)
            if parsed_command:
                statusbar_infos = parsed_command.groupdict()
                action = statusbar_infos["command"]
                if action in self.rogomatic.get_actions():
                    action_log = [Log("action", "Action: {}, Reward: {}".format(action, reward), 2)]
                    self.l.log(action_log)
                    # The action is relevant for this agent configuration, so...
                    action_index = self.rogomatic.get_actions().index(action)
                    # save into the history
                    self.history_manager.update_history(action_index, reward, terminal)
            if not self.rogomatic.is_running():
                dead_log = [Log("dead_log", "We're dead. Kinda. Let's rise again!", 2)]
                self.l.log(dead_log)
                self.starting = True
                self.rogomatic.reset()
            elif self.is_freezed():
                freeze_log = [Log("freeze_log", "Rogomatic froze. Let's kill it with fire!", 2)]
                self.l.log(freeze_log)
                self.starting = True
                self.rogomatic.reset()

# LEARNER AGENTS

class QLearnerAgent(LearnerAgent):
    def __init__(self, configs):
        import models, history
        
        # class instances
        self.rb = RogueBox(configs)
        self.model_manager = getattr(models, configs["model_manager"])(self.rb)
        self.history_manager = getattr(history, configs["history_manager"])(self)
        # configs
        self.configs = configs
        self.configs["iteration"] = 1
        self.configs["actions"] = self.rb.get_actions()
        self.configs["actions_num"] = len(self.configs["actions"])
        # gui stuff
        ui = None
        log_targets = []
        if configs["logsonfile"]:
            log_targets.append("file")
        if self.configs["gui"]:
            self.ui = UIManager.init(configs["userinterface"], self.rb)
            self._pending_action = None
            ui = self.ui
            log_targets.append("ui")
            self.l = Logger(log_depth=configs["verbose"], log_targets=log_targets, ui=ui)
        else:
            log_targets.append("terminal")
            self.l = Logger(log_depth=configs["verbose"], log_targets=log_targets)
        # state
        self.state = self.model_manager.reshape_initial_state(self.rb.compute_state())
        self.old_state = self.state
        # model
        self.model = self.model_manager.build_model()
        self.target_model = self.model_manager.build_model()
        self.target_model.set_weights(self.model.get_weights())
        # resume from file
        # load weights, transitions history and parameters from assets, if any
        self._load_progress()

    def _load_progress(self):
        # model weights
        if os.path.isfile("assets/weights.h5"):
            print("loading weights...")
            self.model.load_weights("assets/weights.h5")
            self.target_model.set_weights(self.model.get_weights())
            print("weights loaded!")

        # transitions history
        if self.configs["save_history"]:
            self.history_manager.load_history_from_file("assets/history.pkl")

        # parameters
        # only float can be loaded like this for now
        if os.path.isfile("assets/parameters.csv"):
            print("loading parameters...")
            with open("assets/parameters.csv") as parameters:
                reader = csv.reader(parameters)
                for row in reader:
                    try:
                        # try conversion from string
                        self.configs[row[0]] = float(row[1])
                    except ValueError:
                        print("the parameter", row[0], " is not a float castable value")
            print("parameters loaded!")

    def _save_progress(self):
        print("saving...")
        if not os.path.exists("assets"):
            os.makedirs("assets")

        print("saving weights...")
        self.model.save_weights("assets/weights.h5", overwrite=True)

        if self.configs["save_history"]:
            self.history_manager.save_history_on_file("assets/history.pkl")

        print("saving parameters...")
        with open("assets/parameters.csv", "w") as parameters:
            writer = csv.writer(parameters)
            writer.writerow(["epsilon", self.configs["epsilon"]])
            writer.writerow(["iteration", self.configs["iteration"]])
        print("done saving!")

    def _reinit(self):
        self.state = self.model_manager.reshape_initial_state(self.rb.compute_state())
        self.old_state = self.state

    def predict(self):
        """return a numpy array of length actions_num all set to 0
        except for the index of the action to take wich is set to 1"""
        # chose an action epsilon greedy
        actions_array = np.zeros(self.configs["actions_num"])
        if random.random() <= self.configs["epsilon"]:
            action_index = random.randrange(self.configs["actions_num"])
        else:
            q = self.model.predict(self.state)
            logs = [ Log("actions_array", "This is the action array: {}".format(q), LOG_LEVEL_MORE)]
            actions = self.configs["actions"]
            if self.configs["only_legal_actions"]:
                legal_actions = self.rb.get_legal_actions()
                for action in actions:
                    if action not in legal_actions:
                        q[(0, actions.index(action))] = -np.inf
            logs += [ Log("legal_actions_array", "This is the legal action array: {}".format(q), LOG_LEVEL_MORE)]
            self.l.log(logs)
            action_index = np.argmax(q)
        return action_index

    def act(self, action_index):
        action = self.configs["actions"][action_index]
        reward, new_state, terminal = self.rb.send_command(action)
        logs = [ Log("action_reward", "Sent action: {} got reward: {}".format(action, reward), LOG_LEVEL_MORE)]
        self.l.log(logs)
        self.old_state = self.state
        self.state = self.model_manager.reshape_new_state(self.old_state, new_state)
        return reward, terminal

    def observe(self):
        timer_log = [Log("Observe_time", "Ten observe done", LOG_LEVEL_MORE, mean=10)]
        self.l.start_log_timer(timer_log)
        minibatch = self.history_manager.pick_batch(self.configs["batchsize"])
        inputs = np.zeros((self.configs["batchsize"],) + self.state.shape[1:])
        targets = np.zeros((self.configs["batchsize"], self.configs["actions_num"]))

        # Now we do the experience replay
        for i in range(self.configs["batchsize"]):
            old_state = minibatch[i][0]
            action_index = minibatch[i][1]
            reward = minibatch[i][2]
            new_state = minibatch[i][3]
            terminal = minibatch[i][4]

            inputs[i] = old_state
            targets[i] = self.model.predict(old_state)

            if terminal:
                targets[i, action_index] = reward
            else:
                Q_new_state = self.target_model.predict(new_state)
                targets[i, action_index] = reward + self.configs["gamma"] * np.max(Q_new_state)

        loss = self.model.train_on_batch(inputs, targets)
        loss_log = [Log("loss_value", "Loss for this iteration: {}".format(loss), LOG_LEVEL_SOME)]
        self.l.log(loss_log)
        self.l.stop_log_timer(timer_log)
        return loss

    def plot(self, frame):
        #WARNING works only with 3 layers states
        #makes sense only with non reshaped, no memory states
        # generate heatmap
        heatmap_start = [Log("heatmap_start", "Generating heatmap for iteration {} ...".format(self.configs["iteration"]), LOG_LEVEL_SOME)]
        self.l.log(heatmap_start)
        heatmap_time = [Log("heatmap_time", "Generating heatmap took", LOG_LEVEL_MORE, mean=1)]
        self.l.start_log_timer(heatmap_time)

        heatmap = np.zeros((22, 80))
        best_actions = np.full((22, 80), -1)
        passable_pos = np.argwhere(frame[0]==255)

        for i, j in passable_pos:
            player_layer = np.zeros((22, 80))
            player_layer[i][j] = 255
            temp = np.stack((frame[0], player_layer, frame[2]))
            q = self.model.predict(self.model_manager.reshape_new_state(temp, temp))
            heatmap[i][j] = q.max()
            best_actions[i][j] = q[0].argmax()

        heatmap = np.ma.masked_where(heatmap==0, heatmap)
        mn = heatmap.min()
        mx = heatmap.max()
        heatmap_start = [Log("minmax", "heatmap min: {} max: {}".format(mn, mx), LOG_LEVEL_SOME)]
        self.l.log(heatmap_start)

        arrows = ['←', '↓', '↑', '→']

        cmap = plt.cm.hot_r
        cmap.set_bad(color="green")
        fig, ax = plt.subplots(figsize=(11,5))
        ax.imshow(heatmap, cmap=cmap, interpolation='nearest', vmin=mn, vmax=mx)
        for i, j in passable_pos:
            ax.text(j, i, '%s' % arrows[best_actions[i][j]], ha='center', va='center')
        fig.savefig("plots/heatmap-iteration-%s.png" % self.configs["iteration"])

    def train(self):
        if self.configs["gui"]:
            self._pending_action = self.ui.on_timer_end(100, lambda: self._train_callback(1))
            self.ui.on_key_press(self._train_key_callback)
            self.ui.start_ui()
        else:
            while True:
                self._train_step(self.configs["iteration"])
                self.configs["iteration"] += 1

    def _train_step(self, iteration):
        action_index = self.predict()
        self._train_evaluation_hook_before_action()
        reward, terminal = self.act(action_index)
        self._train_evaluation_hook_after_action()
        item_added = self.history_manager.update_history(action_index, reward, terminal)
        if iteration % 10 == 0:
            log_iteration = [Log("iteration", "Iteration number: {}".format(self.configs["iteration"]), LOG_LEVEL_SOME)]
            log_iteration += [Log("hist", "History size: {}".format(self.history_manager.hist_len()), LOG_LEVEL_SOME)]
            self.l.log(log_iteration)
        # Begin training only when we have enough history
        if self.history_manager.hist_len() >= self.configs["minhist"] and item_added:
            self.observe()
            # anneal epsilon
            if self.configs["epsilon"] > self.configs["final_epsilon"]:
                self.configs["epsilon"] -= (self.configs["initial_epsilon"] - self.configs["final_epsilon"]) / \
                                              self.configs["explore_steps"]
            logs = [Log("epsilon", "{}".format(self.configs["epsilon"]), LOG_LEVEL_ALL)]
            self.l.log(logs)
            if iteration % 100000 == 0:
                self._save_progress()
                #plottin is disabled because its not compatible with every state
                #uncomment the next line if needed
                #self.plot(self.state[0])
            if iteration % 10000 == 0:
                self.target_model.set_weights(self.model.get_weights())
        if terminal:
            self._train_evaluation_hook_game_over()
            self.rb.reset()
            self._reinit()

    def run(self):
        # dont act randomly
        self.configs["epsilon"] = 0
        if self.configs["gui"]:
            self.ui.on_key_press(self._play_key_callback)
            self._pending_action = self.ui.on_timer_end(100, self._run_callback)
            self.ui.start_ui()
        else:
            terminal = False
            while not terminal:
                self._run_step()

    def _run_step(self):
        action_index = self.predict()
        reward, terminal = self.act(action_index)

    def _train_key_callback(self, event):
        """Callback for keys pressed during learning"""
        if event.char == 'q' or event.char == 'Q':
            self.rb.quit_the_game()
            exit()

    def _play_key_callback(self, event):
        """Callback for keys pressed during playing"""
        if event.char == 'q' or event.char == 'Q':
            self.rb.quit_the_game()
            exit()
        elif event.char == 'r' or event.char == 'R':
            # we need to stop the agent from acting
            # or it will try to write to a closed pipe
            self.ui.cancel_timer(self._pending_action)
            self.rb.reset()
            self._reinit()
            self._pending_action = self.ui.on_timer_end(100, self._run_callback)
            
    def _train_callback(self, iteration):
        self._train_step(iteration)
        self.ui.draw_from_rogue()
        self.configs["iteration"] += 1
        self._pending_action = self.ui.on_timer_end(self.configs["gui_delay"],
                                                   lambda: self._train_callback(self.configs["iteration"]))

    def _run_callback(self):
        self._run_step()
        self.ui.draw_from_rogue()
        if not self.rb.game_over():
            # renew the callback
            self._pending_action = self.ui.on_timer_end(self.configs["gui_delay"], self._run_callback)
        else:
            self.ui.cancel_timer(self._pending_action)

    # evaluation hooks
    def _train_evaluation_hook_before_action(self):
        pass

    def _train_evaluation_hook_after_action(self):
        pass

    def _train_evaluation_hook_game_over(self):
        pass


class QLearnerAgentOnTrial(QLearnerAgent):

    def __init__(self, configs):
        import judges
        super().__init__(configs)
        self.judge = getattr(judges, "SimpleExplorationJudge")(self)
        self._train_evaluation_hook_before_action = self.judge.hook_before_action 
        self._train_evaluation_hook_after_action = self.judge.hook_after_action
        self._train_evaluation_hook_game_over = self.judge.hook_game_over


class PlotterAgent(QLearnerAgent):
    """An agent that plots the first screen Heatmap and then resets
       WARNING works only with 3 layers states
       makes sense only with non reshaped, no memory states
    """
    
    def act(self, action_index):
        reward, new_state, terminal = self.rb.send_command('s')

        self.plot(new_state)

        self.configs["iteration"] += 1
        self.ui.cancel_timer(self._pending_action)
        self.rb.reset()
        self._reinit()
        return None, None

class HistoryAgent(QLearnerAgent):
    """An agent that skips observing
    use it if you only want to build an history
    """

    def plot(self, frame):
        pass

    def observe(self):
        pass
