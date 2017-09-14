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

import argparse
import configparser

class ConfigurationError(Exception):
    """Something is wrong with the provided configuration file."""

class ConfigurationManager:

    def __init__(self):
        # These are default, fallback config
        self.configs = {
            "General": {
                "rogue": "rogue",
                "rogomatic": "rogomatic",
                "mode": "play",
                "agent": "UserAgent",
                "verbose": 0,
                "logsonfile": True,
                "userinterface": "tk",
                "remote_debug": True,
                "gui": False,
                "gui_delay": 100,
            },
            "State": {
                "state_generator": "M_P_D_S_Sn_StateGenerator"
            },
            "Model": {
                "model_manager": "T_5L_Ml_Nr_ModelManager"
            },
            "Reward": {
                "reward_generator": "E_D_Ps_Pp_W_RewardGenerator"
            },
            "History": {
                "history_manager": "FIFORandomPickHM",
                "save_history": False,
                "minhist": 5000,
                "histsize": 100000,
                "keep_balance": False
            },
            "Training": {
                "initial_epsilon": 1,
                "final_epsilon": 0.001,
                "epsilon": 1,
                "explore_steps": 500000,
                "batchsize": 32,
                "gamma": 0.99,
                "only_legal_actions": False
            }
        }
        self.args = None
        # default config file
        self.config_file = "configs/rboxrc"

    def build_configs(self):
        # command line arguments > config file > defaults
        self._parse_command_line()
        self._parse_and_apply_config_file()
        return self.get_configs()

    def get_configs(self):
        #flatten the configs
        configs = {key : value for k, v in self.configs.items() for key, value in v.items()}
        return configs

    def _parse_command_line(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("-c", "--config")
        self.args = parser.parse_args()

    def _parse_and_apply_config_file(self):
        config_file = self.config_file
        if self.args.config is not None:
            from pathlib import Path
            if Path(self.args.config).is_file():
                config_file = self.args.config
            else:
                raise ConfigurationError("Config file '{}' could not be found.".format(self.args.config))
        sections = ["General", "State", "Model", "Reward", "History", "Training"]
        int_options = ["verbose", "explore_steps", "minhist", "histsize", "batchsize", "gui_delay"]
        float_options = ["initial_epsilon", "final_epsilon", "epsilon", "gamma"]
        bool_options = ["gui", "keep_balance", "only_legal_actions", "save_history", "logsonfile", "remote_debug"]
        config = configparser.ConfigParser()
        if config.read(config_file):
            try:
                for section_name in sections:
                    # For every sections...
                    sec_options = config.options(section_name)
                    for option in sec_options:
                        # ... for every option in that section...
                        if option in int_options:
                            self.configs[section_name][option] = config.getint(section_name, option)
                        elif option in float_options:
                            self.configs[section_name][option] = config.getfloat(section_name, option)
                        elif option in bool_options:
                            self.configs[section_name][option] = config.getboolean(section_name, option)
                        else:
                            self.configs[section_name][option] = config.get(section_name, option)
            except:
                raise ConfigurationError("Malformed config file found in '{}'.".format(config_file))
