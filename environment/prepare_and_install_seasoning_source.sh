#!/bin/sh
cd $SEASONING_HOME/
source $SEASONING_HOME/seasoning_conf/secrets

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
  if [ ! -d ~/bin ]; then
    mkdir ~/bin
  fi
  chmod -R 774 seasoning_website/bin
  sudo cp -p seasoning_website/bin/* /usr/local/bin


# Move Apache config

sudo cp /tmp/seasoning.conf /etc/httpd/conf.d/