#!/usr/bin/env python

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

from rogueinabox import RogueBox
from config import ConfigurationManager, ConfigurationError
import agents

def main():

    CM = ConfigurationManager()
    configs = CM.build_configs()

    mode = configs["mode"]
    agent_name = configs["agent"]

    agent = getattr(agents, agent_name)(configs)
    try:
        if mode == "play":
            agent.run()
        elif mode == "learn":
            agent.train()
        else:
            raise AttributeError
    except(AttributeError):
        raise ConfigurationError("Error trying the mode '{}' on the agent '{}': possibly not implemented.".format(mode, agent_name))

if __name__ == "__main__":
    main()
