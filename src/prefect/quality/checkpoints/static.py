"""Checkpoints: full database expectations scan."""

import great_expectations as gx
from expectations.static import NAME as STATIC_SUITE_NAME


def get_static_checkpoint(
    context,
    batch,
    name="static",
    report_by_email: bool = False,
    update_data_docs: bool = False,
):
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

    # This is the default path (relative to the root folder of the Data Context)
    # but can be changed as required
    base_directory = "/app/uncommitted/data_docs/local_site/"
    site_config = {
        "class_name": "SiteBuilder",
        "site_index_builder": {"class_name": "DefaultSiteIndexBuilder"},
        "store_backend": {
            "class_name": "TupleFilesystemStoreBackend",
            "base_directory": base_directory,
        },
    }
    site_name = "my_data_docs_site"
    if site_name not in context.list_data_docs_sites():
        context.add_data_docs_site(site_name=site_name, site_config=site_config)
    if update_data_docs:
        action_list.append(
            gx.checkpoint.actions.UpdateDataDocsAction(
                name="update_my_site", site_names=[site_name]
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
