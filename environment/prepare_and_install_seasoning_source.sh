#!/bin/sh
cd $SEASONING_HOME

### PREPARE CONFIGURATION ###

# Prepare apache configuration

sed "s#\*SEASONING_HOME\*#$SEASONING_HOME#" seasoning_website/apache/seasoning.conf > /tmp/seasoning.conf


# Prepare django configuration

echo "TODO: insert passwords etc in django settings files"



### MOVE FILES ###

# Add Seasoning commands to path

  # Check if bin directory is present
  if [ ! -d ~/bin ]; then
    mkdir ~/bin
  fi
  chmod -R 774 seasoning_website/bin
  cp -p seasoning_website/bin/* ~/bin


# Move Apache config

sudo cp /tmp/seasoning.conf /etc/httpd/conf.d/


# Set Django in Production Mode

echo "TODO: Switch deployment setting files"

