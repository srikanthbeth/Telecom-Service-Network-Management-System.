from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

from core.config import settings
from db.database import Base

# Import models so Alembic can detect them
from models.user import User
from models.auth_token import AuthToken
from models.customer import Customer
from models.customer_history import CustomerHistory
from models.plan import Plan
from models.sim import SIM
from models.sim_replacement_history import SIMReplacementHistory
from models.device import Device
from models.device_sim_mapping import DeviceSIMMapping
from models.subscription import Subscription
from models.subscription_history import SubscriptionHistory

from models.tower import Tower

from models.technician import Technician
from models.technician_skill import TechnicianSkill
from models.technician_assignment import TechnicianAssignment
from models.support_ticket import SupportTicket
from models.ticket_comment import TicketComment
from models.ticket_history import TicketHistory
from models.service_request import ServiceRequest
from models.service_request_history import ServiceRequestHistory

# Alembic Config object
config = context.config


# Configure Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# SQLAlchemy metadata for autogenerate
target_metadata = Base.metadata


# Use DATABASE_URL from .env
config.set_main_option(
    "sqlalchemy.url",
    settings.DATABASE_URL,
)


def run_migrations_offline() -> None:
    """Run migrations in offline mode."""

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named"
        },
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in online mode."""

    connectable = engine_from_config(
        config.get_section(
            config.config_ini_section,
            {}
        ),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()