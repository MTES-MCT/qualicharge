"""Checkpoints: full database expectations scan."""

import great_expectations as gx
import great_expectations.expectations as gxe

from expectations.pdc import get_expectation_suite as pdc_get_expectation_suite


def get_full_checkpoint(context, batch, name="full"):
    """Get the full checkpoint."""
    definition_name = "my_validation_definition"
    validation_definition = gx.ValidationDefinition(
        data=batch, suite=pdc_get_expectation_suite(context), name=definition_name
    )
    validation_definition = context.validation_definitions.add(validation_definition)

    action_list = [
        gx.checkpoint.EmailAction(
            notify_on="all",
            name="dunno",
            receiver_emails="${GX_RECEIVER_EMAILS}",
            smtp_address="${GX_BREVO_SMTP_ADDRESS}",
            smtp_port="${GX_BREVO_SMTP_PORT}",
            sender_login="${GX_BREVO_SENDER_LOGIN}",
            sender_password="${GX_BREVO_PASSWORD}",
            use_tls=True,
        )
    ]

    # Create a check point
    checkpoint = gx.Checkpoint(
        name=name,
        validation_definitions=[
            validation_definition,
        ],
        actions=action_list,
        result_format={"result_format": "COMPLETE"},
    )
    context.checkpoints.add(checkpoint)
    return checkpoint
