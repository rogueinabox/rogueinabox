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

all: install

ENV_DIR ?= .env

run:
	( \
		. $(ENV_DIR)/bin/activate; \
		python run.py; \
	)

install: makeenv installdeps

makeenv:
	if [ ! -d "$(ENV_DIR)" ]; then \
		virtualenv -p python3 $(ENV_DIR); \
	fi

installdeps:
	( \
		. $(ENV_DIR)/bin/activate; \
		pip install --upgrade pip; \
		pip install -r requirements.txt; \
		git clone https://github.com/Theano/libgpuarray.git /tmp/_libgpuarray_git; \
		cd /tmp/_libgpuarray_git; \
		git checkout v0.6.5; \
		python setup.py build; \
		python setup.py install; \
		rm -rf /tmp/_libgpuarray_git; \
	)

clean:
	rm -rf $(ENV_DIR)
