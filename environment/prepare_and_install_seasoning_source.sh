# Copyright 2012, 2013 Driesen Joep
# 
# This file is part of Seasoning.
# 
# Seasoning is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Seasoning is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Seasoning.  If not, see <http://www.gnu.org/licenses/>.
#     

#!/bin/sh
cd $SEASONING_HOME/
source $SEASONING_HOME/seasoning_config/secrets

### PREPARE CONFIGURATION ###

# Prepare apache configuration

sed "s#\*SEASONING_HOME\*#$SEASONING_HOME#g" seasoning_website/apache/seasoning.conf > /tmp/seasoning.conf


# Prepare django configuration

sed "s#\*SEASONING_HOME\*#$SEASONING_HOME#g" seasoning_website/Seasoning/Seasoning/deploy_settings.py | \
sed "s#\*DATABASE_NAME\*#$DATABASE_NAME#g" | \
sed "s#\*DATABASE_USER\*#$DATABASE_USER#g" | \
sed "s#\*DATABASE_PASSWORD\*#$DATABASE_PASSWORD#g" | \
sed "s#\*SECRET_KEY\*#$SECRET_KEY#g" | \
sed "s#\*EMAIL_HOST_PASSWORD\*#$EMAIL_HOST_PASSWORD#g" | \
sed "s#\*RECAPTCHA_PRIVATE_KEY\*#$RECAPTCHA_PRIVATE_KEY#g" > seasoning_website/Seasoning/Seasoning/settings.py


### MOVE FILES ###

# Add Seasoning commands to path

  # Check if bin directory is present
  chmod -R 774 seasoning_website/bin
  sudo cp -p seasoning_website/bin/* /usr/local/bin
  
  # Always use current version
  sed "s/SEASONING_VERSION=.*/SEASONING_VERSION=$1/" /etc/profile.d/seasoning.sh > /tmp/seasoning.sh
  sudo mv /tmp/seasoning.sh /etc/profile.d/seasoning.sh


# Move Apache config

sudo cp /tmp/seasoning.conf /etc/httpd/conf.d/