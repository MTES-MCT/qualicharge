#!/usr/bin/env bash

#
# Dependencies
#
# - curl
# - expect
# - jq
# - bw (BitWarden CLI)
# - scalingo (Scalingo CLI)
# - xkcdpass (password generator)
#
# To run this script, we expect the following environment variables to be defined:
#
# Vaultwarden
#
# export BW_CLIENTID
# export BW_CLIENTSECRET
# export BW_PASSWORD
#
# Brevo
#
# export BREVO_API_KEY
#

set -eo pipefail

declare SCRIPTS_DIR
SCRIPTS_DIR="$(dirname "$0")"

# Load libraries
# shellcheck source=scripts/_common.sh
source "${SCRIPTS_DIR}/_common.sh"

# Script usage
function usage() {

  local -i exit_code=${1:-0}

  echo "Usage: reset-password USERNAME"

  exit ${exit_code}
}

# Reset user password
function reset_password() {

  local email
  local firstname
  local password
  local send_password
  local username="${1:-}"

  if [[ -z "${username}" ]]; then
    echo -e "No username provided.\n"
    usage 10
  fi

  # Export this function so that expect can run it in a forked process
  export -f qualicharge

  echo "⚙️ Will reset password for API user ${username}"

  # Get user first name and email
  # nota bene: the sed pattern removes ANSI colors from piped stdout (json)
  read -r firstname email <<<$( \
    qualicharge read-user "${username}" --json | \
      grep -A 100 "{" | \
      sed -r "s/[[:cntrl:]]\[[0-9]{1,3}m//g" | \
      jq -r ".first_name,.email" | \
      xargs \
  )

  password=$(generate_password)

  expect -c "
  spawn bash -c \"qualicharge update-user ${username} --set-password\"
  expect \"*Password*\" {send -- \"${password}\n\"}
  expect \"*Confirm*\" {send -- \"${password}\n\"}
  expect \"*Apply*\" {send -- \"y\n\"}
  interact
  exit
  "

  send_password=$(generate_password)
  send_url=$(
    bw_send \
      "${username}" \
      "${password}" \
      "${send_password}"
  )

  email_send_link "${email}" "${firstname}" "${send_url}"
  sleep 1

  email_send_password "${email}" "${firstname}" "${send_password}"
}

reset_password "$@"
