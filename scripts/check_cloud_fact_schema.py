from sqlalchemy import inspect

from src.database.connection import get_engine

engine = get_engine()
inspector = inspect(engine)

table = "fact_cloud_usage"
schema = "warehouse"

print("=" * 80)
print("FACT CLOUD USAGE CONSTRAINTS")
print("=" * 80)

print("\nPRIMARY KEY:")
print(
    inspector.get_pk_constraint(
        table,
        schema=schema,
    )
)

print("\nUNIQUE CONSTRAINTS:")
for constraint in inspector.get_unique_constraints(
    table,
    schema=schema,
):
    print(constraint)

print("\nINDEXES:")
for index in inspector.get_indexes(
    table,
    schema=schema,
):
    print(index)

print("\nCOLUMNS:")
for column in inspector.get_columns(
    table,
    schema=schema,
):
    print(
        column["name"],
        "|",
        column["type"],
        "| nullable:",
        column["nullable"],
    )
