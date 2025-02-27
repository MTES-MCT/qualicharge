"""Checkpoints: full database expectations scan."""

import great_expectations as gx
import great_expectations.expectations as gxe

from expectations.pdc import get_expectation_suite


def get_static_checkpoint(context, batch, name="static"):
    """Get the static checkpoint."""
    definition_name = "static_validation_definition"
    validation_definition = gx.ValidationDefinition(
        data=batch, suite=get_expectation_suite(context), name=definition_name
    )
    validation_definition = context.validation_definitions.add(validation_definition)

    action_list = [
        gx.checkpoint.EmailAction(
            notify_on="all",
            name="Static expectations report",
            receiver_emails="${GX_RECEIVER_EMAILS}",
            smtp_address="${GX_BREVO_SMTP_ADDRESS}",
            smtp_port="${GX_BREVO_SMTP_PORT}",
            sender_login="${GX_BREVO_SENDER_LOGIN}",
            sender_alias="Julien M.",
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
