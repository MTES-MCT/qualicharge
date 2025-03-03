"""Checkpoints: full database expectations scan."""

import great_expectations as gx
from expectations.static import NAME as STATIC_SUITE_NAME


def get_static_checkpoint(context, batch, name="static", report_by_email: bool = False):
    """Get the static checkpoint."""
    # definition_name = "static_validation_definition"
    suite = context.suites.get(STATIC_SUITE_NAME)
    validation_definition = gx.ValidationDefinition(data=batch, suite=suite, name=name)
    validation_definition = context.validation_definitions.add(validation_definition)

    action_list = []
    if report_by_email:
        action_list.append(
            gx.checkpoint.EmailAction(
                notify_on="all",
                name="Static expectations report",
                receiver_emails="${GX_RECEIVER_EMAILS}",
                smtp_address="${GX_BREVO_SMTP_ADDRESS}",
                smtp_port="${GX_BREVO_SMTP_PORT}",
                sender_login="${GX_BREVO_SENDER_LOGIN}",
                sender_alias="QualiCharge Bot <contact@qualicharge.beta.gouv.fr>",
                sender_password="${GX_BREVO_PASSWORD}",
                use_tls=True,
            )
        )

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
