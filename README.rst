===========
Faxcelerate
===========

Faxcelerate is free software: you can redistribute it and/or modify
it under the terms of version 3 of the GNU Affero General Public
License, as published by the Free Software Foundation.

Faxcelerate is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public
License along with Faxcelerate.  If not, see
<http://www.gnu.org/licenses/>.

Introduction
============

Faxcelerate is a web interface for HylaFAX. It has been developed 
mostly as a tool for fax archival, searching and retrieval in a 
multi-user environment, but it also offers a quick interface for 
sending fax messages. 

Installation
============

Beside a working installation of Hylafax, you will need:
- Python 2.5 or later with virtualenv.
- The Git version control software
- a web server that supports WSGI (here Apache is shown as an example, 
but you can choose your favourite one).
- A database server, like PostgreSQL
- The Django web framework
-

In this case, on a Debian/Ubuntu system, you would run::

	apt-get install python-virtualenv git libapache2-mod-wsgi 
	postgresql libpq-dev libjpeg-dev python-dev gettext

Some knowledge of the Django web framework is very helpful. 

In this example we'll use the following paths:

- ``/var/spool/hylafax`` for the HylaFAX spool directory;
- ``/var/local/faxcelerate-env`` for Faxcelerate's virtual environment.

1.	Create the virtual environment by typing in a shell::

		virtualenv /var/local/faxcelerate-env
		
#.	Let the shell use the virtual environment::

		cd /var/local/faxcelerate-env
		. ./bin/activate

#.	Download and install the Faxcelerate source code::

		pip install -e git://github.com/puccia/faxcelerate#egg=faxcelerate
	
	(pip will complain about the lack of a ``setup.py`` file; this will be provided in a future release.)

	Now the code will be in 
	``/var/spool/faxcelerate-env/src/faxcelerate;`` you will thus find:

	-	the Django project ``faxcelerate`` rooted at 
		``/var/local/faxcelerate-env/src/faxcelerate/faxcelerate``

	-	the Django application ``fax`` rooted at 
		``/var/local/faxcelerate-env/src/faxcelerate/faxcelerate/fax``.

#.	Install the Python prerequisites::

		cd /var/local/faxcelerate-env/src/faxcelerate
		pip install -r requirements.txt

#.	Create a database, if you are not using sqlite. For example, if you
	are using PostgreSQL::
	
		su postgres
		createuser -d -R -S -P faxcelerate
		echo "CREATE DATABASE \"faxcelerate\" OWNER faxcelerate ENCODING 'UTF-8' LC_TYPE='en_US.UTF-8' LC_COLLATE='en_US.UTF-8' TEMPLATE template0" | LANG=en_US.UTF-8 psql
		exit


#.	Edit the ``local_settings.py`` file in the project directory to suit 
	your configuration::

		cd faxcelerate
		
#.	Now execute::

		python manage.py syncdb
	
	to create and initialise the database. You will be asked for the 
	superuser's username and password.

#.	Execute::

		python manage.py migrate

#.	Compile the localized message files::

		cd fax
		python ../manage.py compilemessages

#.	Configure your web server to run the Django project. If you are 
	using Apache, you can use the supplied ``apache/faxcelerate.conf``
	file to configure a suitable virtual host, and the supplied 
	``apache/django.wsgi`` file to run the WSGI application. Please 
	note that the software runs with the same UID/GID as HylaFAX.
	
#.	Edit ``bin/faxrcvd`` and ``bin/notify`` in your HylaFAX directory.
	This is needed to automatically file and index every processed 
	incoming and outgoing fax message. In ``faxrcvd``, right after the 
	syntax check, you can add::
	
		/var/local/faxcelerate-env/bin/python /var/local/faxcelerate-env/src/faxcelerate/faxcelerate/bin/faxrcvd.py "$1" "$2" "$3" "$4" "$5" "$6" "$7"

	In ``notify`` you can add::
	
		/var/local/faxcelerate-env/bin/python /var/local/faxcelerate-env/src/faxcelerate/faxcelerate/bin/notify.py "$1" "$2" "$3" "$4" "$5" "$6" "$7" "$8" "$9"
