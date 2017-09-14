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

import sys, tempfile, os, datetime, glob
from subprocess import call
from shutil import copyfile

# directories
default_assets_dir = "../assets"
default_config_dir = "../configs"
save_dir = default_assets_dir + "/saves"
# default values
default_history = "history.pkl"
default_weights = "weights.h5"
default_logfile = "very_long_logfile.log"
# today
today = datetime.datetime.now()
this_save = save_dir + "/" + today.strftime("%Y%m%d_%H%M%S")

print("\n== Rogueinabox savestate utility ==\n")
proceed = input("Saves will be located in '{}' . Proceed? [Y / n] ".format(os.path.abspath(this_save)))
if proceed=="" or proceed.lower()=="y":
    tag = input(" > Append a tag to the folder name? (empty means none) ")
    # prepare dirs
    if not os.path.exists(os.path.abspath(save_dir)):
        os.makedirs(os.path.abspath(save_dir))
    if not tag=="":
        this_save = this_save + "-" + tag
    if not os.path.exists(os.path.abspath(this_save)):
        os.makedirs(os.path.abspath(this_save))
        hist_save = log_save = config_save = weights_save = False

        # MESSAGE
        commit = input("Do you want to write a save message? [Y / n] ")
        if commit=="" or commit.lower()=="y":
            EDITOR = os.environ.get('EDITOR','vim')
            initial_message = "\n\n#\n# Save done on " + str(today)
            initial_message = bytes(initial_message, "utf-8")
            with tempfile.NamedTemporaryFile(suffix=".tmp") as tf:
                tf.write(initial_message)
                tf.flush()
                call([EDITOR, tf.name])
                copyfile(tf.name, os.path.abspath(this_save + "/save_msg.txt"))

        # HISTORY
        hist = input("Do you want to save the history? [y / N] ")
        if hist.lower()=="y":
            hist_name = input(" > Do you want to rename the history file? (empty means {}) ".format(default_history))
            if hist_name=="":
                hist_name = default_history
            hist_save = True


        # WEIGHTS
        weights = input("Do you want to save the weights? [Y / n] ")
        if weights=="" or weights.lower()=="y":
            weights_name = input(" > Do you want to rename the weights file? (empty means {}) ".format(default_weights))
            if weights_name=="":
                weights_name = default_weights
            weights_save = True

        # CONFIG
        config = input("Do you want to save the config file? [Y / n] ")
        if config=="" or config.lower()=="y":
            files = []
            list_of_files = glob.glob(default_config_dir + "/*")
            latest_file = os.path.basename(os.path.abspath(max(list_of_files, key=os.path.getctime)))
            print(" > Here are your configs...")
            for f in list_of_files:
                print("\t" + os.path.basename(os.path.abspath(f)))
            config_name = input(" > ...which one do you want me to save? (empty means {}) ".format(latest_file))
            if config_name=="":
                config_name = latest_file
            config_save = True

        # LOGFILE
        logs = input("Do you want to save the logs? [y / N] ")
        if logs.lower()=="y":
            log_name = input(" > Do you want to rename the log file? (empty means {}) ".format(default_logfile))
            if log_name=="":
                log_name = default_logfile
            log_save = True

        # Save process
        print("\n > Alright! Now saving...")
        if hist_save:
            copyfile(default_assets_dir + "/" + default_history, this_save + "/" + hist_name) 
            print(" >>> history saved")
        if weights_save:
            copyfile(default_assets_dir + "/" + default_weights, this_save + "/" + weights_name) 
            print(" >>> weights saved")
        if config_save:
            copyfile(default_config_dir + "/" + config_name, this_save + "/config_" + config_name) 
            print(" >>> config saved")
        if log_save:
            copyfile(default_assets_dir + "/" + default_logfile, this_save + "/" + log_name) 
            print(" >>> logs saved")


print("\nDone. Bye!")
