#!/usr/bin/env bash

set -euo pipefail

# Constants
declare BREVO_SMTP_EMAIL_ENDPOINT="https://api.brevo.com/v3/smtp/email"
declare SCALINGO_APP="${SCALINGO_APP:-qualicharge-api-staging}"
declare ENVIRONMENT="${ENVIRONMENT:-staging}"

if [ "${ENVIRONMENT}" = "production" ]; then
  SCALINGO_APP="qualicharge-api"
fi

echo "Environment: ${ENVIRONMENT} - ${SCALINGO_APP}"

# Password generator
function generate_password() {
  xkcdpass -d "-"
}

# QualiCharge API
function qcm() {

  scalingo \
    --app "${SCALINGO_APP}" \
    --region osc-fr1 \
    run --silent \
    qcm "$@"
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
      --arg pass "${pass}" --arg user "${user}" \
      '.text.text="username: " + $user + "\npassword: " + $pass | .text.hidden=true' | \
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
    --url "${BREVO_SMTP_EMAIL_ENDPOINT}" \
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
        environment: $environment,
        send_url: $url
     }
  }'

  # Compile jq template
  payload=$( \
    jq -nc \
      --arg email "${email}" \
      --arg firstname "${firstname}" \
      --arg environment "${ENVIRONMENT}" \
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
