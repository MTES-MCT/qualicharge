#!/usr/bin/env bash

set -eo pipefail

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

declare SCRIPTS_DIR
SCRIPTS_DIR="$(dirname "$0")"
declare GROUPS_CSV_FILENAME="${SCRIPTS_DIR}/groups.csv"
declare USERS_CSV_FILENAME="${SCRIPTS_DIR}/users.csv"

# Password generator
function generate_password() {
  xkcdpass -d "-"
}

# QualiCharge API
function qualicharge() {

  # Scalingo command is eating stdin preventing iteration over a file for
  # example. Fixing this by sending empty stdin.
  echo "" | scalingo \
    --app qualicharge-api \
    --region osc-fr1 \
    run --silent \
    python -m qualicharge "$@"
}

# Create API group
function api_group() {

  # Group name
  local group="${1}"
  # Operational units (separated by commas)
  local ou="${2//,/ --operational-units }"

  echo "⚙️ Will create API group ${group}"

  # shellcheck disable=SC2068
  qualicharge create-group --force "${group}" --operational-units ${ou[@]}
}

# Create API user
function api_user() {

  local username="${1}"
  local firstname="${2}"
  local lastname="${3}"
  local email="${4}"
  local password="${5}"
  local groups="${6//,/ --groups }"

  echo "⚙️ Will create API user ${username}"

  # shellcheck disable=SC2068
  qualicharge create-user --force \
    --first-name "${firstname}" \
    --last-name "${lastname}" \
    --email "${email}" \
    --groups ${groups[@]} \
    --password "${password}" \
    --scopes "static:create" \
    --scopes "static:read" \
    --scopes "static:update" \
    --scopes "dynamic:create" \
    "${username}"
}

# Create a Vaultwarden send with the user password
function bw_send() {

  local user="${1}"
  local pass="${2}"
  local send_password="${3}"
  local send_url

  if ! bw login --check > /dev/null; then
    bw login --apikey
  fi

  # Unlock Vault and get a session key
  if ! bw unlock --check > /dev/null; then
    BW_SESSION=$(bw unlock --raw --passwordenv BW_PASSWORD)
    export BW_SESSION
  fi

  # Create a send with the user password
  send_url=$(bw send template send.text | \
    jq \
      '.notes="This send should stay private. It expires in 5 days."' | \
    jq \
      --arg user "${user}" \
      '.name="QualiCharge API access - " + $user' | \
    jq \
      --arg pass "${pass}" \
      '.text.text="Your API password is: " + $pass | .text.hidden=true' | \
    jq \
      --arg send_password "${send_password}" \
      '.password=$send_password | .maxAccessCount=3' | \
    jq \
      --arg exp "$(date --iso-8601=s -d '+5 days')" \
      '.expirationDate=$exp' | \
    bw encode | \
    bw send create | \
    jq -r '.accessUrl'
  )

  echo "${send_url}"
}

# Send a transactional email using Brevo
function brevo_email() {

  local payload="${1}"

  curl --request POST \
    --url https://api.brevo.com/v3/smtp/email \
    --header "accept: application/json" \
    --header "api-key: ${BREVO_API_KEY}" \
    --header "content-type: application/json" \
    --data "${payload}"
}

# Send the BW send link by email
function email_send_link() {

  local email="${1}"
  local firstname="${2}"
  local url="${3}"
  local tpl
  local payload

  echo "✉️ Will send BW send link to ${email}"

  # Payload jq template
  # shellcheck disable=SC2016
  tpl='{
     to: [
        {
           email: $email
        }
     ],
     templateId: 1,
     params:{
        first_name: $firstname,
        send_url: $url
     }
  }'

  # Compile jq template
  payload=$( \
    jq -nc \
      --arg email "${email}" \
      --arg firstname "${firstname}" \
      --arg url "${url}" \
      -f <(echo "${tpl}")
  )

  brevo_email "${payload}"
}

# Send the BW send password by email
function email_send_password() {

  local email="${1}"
  local firstname="${2}"
  local send_password="${3}"
  local tpl
  local payload

  echo "✉️ Will send BW send password to ${email}"

  # Payload jq template
  # shellcheck disable=SC2016
  tpl='{
     to: [
        {
           email: $email
        }
     ],
     templateId: 2,
     params:{
        first_name: $firstname,
        send_password: $send_password
     }
  }'

  # Compile jq template
  payload=$( \
    jq -nc \
      --arg email "${email}" \
      --arg firstname "${firstname}" \
      --arg send_password "${send_password}" \
      -f <(echo "${tpl}")
  )

  brevo_email "${payload}"
}

# Create users and groups
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

    api_group "${name}" "${ou}"
  done < <(tail -n +2 "${GROUPS_CSV_FILENAME}")
}

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
    api_user \
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
