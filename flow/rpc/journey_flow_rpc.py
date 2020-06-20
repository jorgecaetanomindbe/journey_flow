from nameko.rpc import rpc
from nameko.standalone.rpc import ClusterRpcProxy

from flow.business.repository.journey_customer_repository import JourneyCustomerRepository


class JourneyFlowRpc:
    """
    Classe RPC para lidar com o tratamento do fluxo do SmartJourney
    """

    name = 'journey_flow'

    @rpc
    def navigate(self, journey_instance_id: str):
        print(f'Sinalizando avanço de navegação para o JourneyInstanceID: [{journey_instance_id}]')

    @rpc
    def start_jounrney_state_expire(self, journey_instance_id: str, time: int):
        print(f'Sinalizando inicio de monitoração de TTL para o JourneyInstanceID: [{journey_instance_id}]. '
              f'Em [{time}] segundos')

        with ClusterRpcProxy() as _rpc:
            res = _rpc.journey_monitor.set_expire(journey_instance_id, time)
        print(res)

    @rpc
    def join_customer_journey(self, journey_name: str, shelf_id: str, journey_data: dict):
        data = {
            'journey_name': journey_name,
            'shelf_id': shelf_id,
            'data': journey_data
        }

        res = JourneyCustomerRepository().insert_one(data)
        journey_instance_id = res['_id']

        print(f'JourneyInstanceID [{journey_instance_id}] Inserido. Relacionando a Jornada [{journey_name}] com o '
              f'Customer [{shelf_id}]')

        return {'journey_instance_id': journey_instance_id}
