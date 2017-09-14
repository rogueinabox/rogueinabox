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

import time

from datetime import datetime


class Log():
    """TODO"""

    def __init__(self, name, text, depth, every=1, mean=None):
        """Constructor for log"""
        self.name = name
        self.text = text
        self.depth = depth
        self.every = every
        self.mean = mean


class Logger():
    """TODO"""

    def __init__(self, log_depth=0, log_targets=["terminal"], ui=None):
        """Constructor for Logger"""
        self.depth = log_depth
        self.ui = ui
        self.targets = log_targets
        self.timers = {}
        self.every = {}
        self.means = {}
        if "file" in log_targets:
            self.log_file = open("assets/very_long_logfile.log","a+")
        current_time = datetime.now().isoformat()
        text = "\n\n[ Started session at {} ]\n\n ".format(current_time)
        self._print(text)

    def log(self, logs, condition=True):
        """Print the given log on the medium defined in the settings if the depth is right. An addition 'condition'
        gets evaluated before execution. It's possible to print the log text every 'every' cycle."""
        if condition:
            for log in logs:
                if log.depth <= self.depth:
                    if log.every > 1:
                        if log.name not in self.every:
                            self.every[log.name] = 1
                        else:
                            self.every[log.name] += 1
                            if self.every[log.name] >= log.every:
                                self.every[log.name] = 0
                                self._print(log.text)
                    else:
                        self._print(log.text)

    def start_log_timer(self, logs, condition=True):
        """Start a timer count on the given log if the depth is right. If log.mean is more than one
        a mean is started/updated. An addition 'condition' gets evaluated before execution."""
        if condition:
            for log in logs:
                if log.depth <= self.depth:
                    if log.mean>1 and log.name not in self.means:
                        # very first time of a mean request
                        self.means[log.name] = [0, 0]
                    # init the timer
                    self.timers[log.name] = time.time()

    def stop_log_timer(self, logs, condition=True):
        """Stop a timer count on the given log if the depth is right. If log.mean is more than one a mean is
        updated/the relative log.text is printed on the medium specified in the settings. An addition 'condition'
        gets evaluated before execution. """
        if condition:
            for log in logs:
                if log.depth <= self.depth and log.name in self.timers:
                    elapsedTime = time.time() - self.timers[log.name]
                    self.timers.pop(log.name) # reset the timer
                    if log.mean > 1 and log.name in self.means:
                        # update the timer mean
                        self.means[log.name][0] += elapsedTime
                        self.means[log.name][1] += 1
                        if self.means[log.name][1] >= log.mean:
                            mean = self.means[log.name][0] / log.mean
                            self.means.pop(log.name)
                            self._print('{} cycles of [{}] took a mean of {} ms to execute'.format(
                                log.mean, log.text, int(mean * 1000)))
                    else:
                        self._print('[{}] : {} ms'.format(
                            log.text, int(elapsedTime * 1000)))

    def _print(self, string):
        """TODO docs"""
        for target in self.targets:
            if target == "terminal":
                print(string)
            elif target == "file":
                current_time = datetime.now().isoformat()
                text = "[{}] {}\n".format(current_time, string)
                self.log_file.write(text)
            elif target == "ui" and self.ui is not None:
                self.ui.draw_log(string)

