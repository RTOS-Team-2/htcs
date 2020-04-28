#!/usr/bin/env bash

mkdir -p "${HOME}/.local"

install_submodule () {
  echo "Installing $1"

  rm -rf "$1/build"
  mkdir -p "$1/build"

  (cd "$1/build" && \
  cmake -DCMAKE_INSTALL_PREFIX:PATH="${HOME}/.local" .. && \
  make install)

  echo "#######################"
  echo "Successfully installed $1 under ${HOME}/.local"
  echo "#######################"
}

install_submodule "paho.mqtt.c"
