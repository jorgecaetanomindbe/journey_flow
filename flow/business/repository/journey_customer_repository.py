from flow.libs.databases.storage.resource import storage_resource
from flow.libs.databases.storage.crud_base import CrudBase


@storage_resource(
    database='smart_journey',
    subject='journey_customer'
)
class JourneyCustomerRepository(CrudBase):
    pass
