#!/usr/bin/env bash

#
# Dependencies
#
# - curl
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

set -euo pipefail

declare SCRIPTS_DIR
SCRIPTS_DIR="$(dirname "$0")"

# Load libraries
source "${SCRIPTS_DIR}/_common.sh"

# Globals
declare GROUPS_CSV_FILENAME="${SCRIPTS_DIR}/groups.csv"
declare USERS_CSV_FILENAME="${SCRIPTS_DIR}/users.csv"

# Create API group
function create_group() {

  # Group name
  local group="${1}"
  # Operational units (separated by commas)
  local ou="${2//,/ --operational-units }"

  echo "⚙️ Will create API group ${group}"

  # shellcheck disable=SC2068
  # Scalingo command is eating stdin preventing iteration over a file for
  # example. Fixing this by sending empty stdin.
  echo "" | qualicharge create-group --force "${group}" --operational-units ${ou[@]}
}

# Create API user
function create_user() {

  local username="${1}"
  local firstname="${2}"
  local lastname="${3}"
  local email="${4}"
  local password="${5}"
  local groups="${6//,/ --groups }"

  echo "⚙️ Will create API user ${username}"

  # shellcheck disable=SC2068
  # Scalingo command is eating stdin preventing iteration over a file for
  # example. Fixing this by sending empty stdin.
  echo "" | qualicharge create-user --force \
    --first-name "${firstname}" \
    --last-name "${lastname}" \
    --email "${email}" \
    --groups ${groups[@]} \
    --password "${password}" \
    --scopes "static:create" \
    --scopes "static:read" \
    --scopes "static:update" \
    --scopes "dynamic:create" \
    --scopes "dynamic:read" \
    "${username}"
}

# Create groups
function create_groups() {

  local name
  local ou

  echo "💾Will create groups from ${GROUPS_CSV_FILENAME}"

  while IFS=";" read -r name ou
  do
    if [[ -z "${name}" ]]; then continue; fi

    # Trim strings
    name=$(echo "${name}" | xargs)
    ou=$(echo "${ou}" | xargs)

    create_group "${name}" "${ou}"
  done < <(tail -n +2 "${GROUPS_CSV_FILENAME}")
}

# Create users
function create_users() {

  local email
  local firstname
  local groups
  local lastname
  local password
  local send_password
  local send_url
  local username

  echo "💾Will create users from ${USERS_CSV_FILENAME}"

  while IFS=";" read -r firstname lastname username email groups
  do
    if [[ -z "${username}" ]]; then continue; fi

    # Trim strings
    firstname=$(echo "${firstname}" | xargs)
    lastname=$(echo "${lastname}" | xargs)
    username=$(echo "${username}" | xargs)
    email=$(echo "${email}" | xargs)
    groups=$(echo "${groups}" | xargs)

    password=$(generate_password)
    create_user \
      "${username}" \
      "${firstname}" \
      "${lastname}" \
      "${email}" \
      "${password}" \
      "${groups}"

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
  done < <(tail -n +2 "${USERS_CSV_FILENAME}")
}

# Main
create_groups
create_users
