import logging
import os
from concurrent import futures
import grpc
import items_pb2
import items_pb2_grpc

logging.basicConfig(level=logging.INFO)

SERVICE_NAME = os.getenv('SERIVE_NAME', 'items-grpc-service')
GRPC_PORT = int(os.getenv('GRPC_PORT', '50051'))

items = {
    'event1': {
                "name": "AWS Conference",
                "date": "Sep.30.2026 - Oct.10.2026",
                "status": "open",
                "location": "Lepzig",
                "id": "event1",
    },

    'event2': {
                "name": "Microsoft confrence",
                "date": "Sep.30.2026 - Oct.10.2026",
                "status": "open",
                "location": "Lepzig",
                "id": "event2",
        
    },

    'event3': {

                "name": "Dell Conference",
                "date": "Sep.30.2026 - Oct.10.2026",
                "status": "open",
                "location": "Lepzig",
                "id": "event3",
    }

    }

next_id = 4

def to_proto(item):
    return items_pb2.Item(
        id=item['id'],
        date=item['date'],
        name=item['name'],
        status=item['status'],
        location=item['location']
    )

def validate_request(request):
    return None


class ItemService(items_pb2_grpc.ItemServiceServicer):
    def GetItemById(self, request, context):
        logging.info('GetItemById id=%s', request.id)

        item = items.get(request.id)
        if item is None:
            context.abort(
                grpc.StatusCode.NOT_FOUND,
                f'Item with id {request.id} does not exists',
            )

        return to_proto(item)



    def ListItems(self, request, context):
        logging.info('ListItems')

        for item in items.values():
            yield to_proto(item)

    def ListItemsByStatus(self, request, context):
        logging.info('ListItemsByStatus status=%s', request.status)

        matches = [item for item in items.values() if item['status'] == request.status]

        if not matches:
            logging.info('No items found with status=%s', request.status)

        for item in matches:
            yield to_proto(item)

    def AddItems(self, request_iterator, context):
        global next_id
        logging.info('AddItems stream started')
        created_count = 0

        #iterate through client stream as item arrive

        for create_req in request_iterator:
            new_id = f'event{next_id}'
            next_id += 1

            items[new_id] = {
                'name': create_req.name,
                'date': create_req.date,
                'status': create_req.status,
                'location': create_req.location,
                'id':new_id
            }
            created_count += 1

        return items_pb2.AddItemResult(
            created_count = created_count,
            total_count = len(items)
            )
        
        #context.abort(grpc.StatusCode.UNIMPLEMENTED, 'AddItems not implemented')


    def ChatAbouttItem(self, request_iterator, context):
        logging.info('ChatAboutItems stream started')

        for chat_msg in request_iterator:
            logging.info('received chat message from %s: %s', chat_msg.sender, chat_msg.message)

            yield items_pb2.ChatMessage(
                sender='Server Bot',
                message=f'received message {chat_msg.sequence}:\'{chat_msg.message}\'',
                sequence=chat_msg.sequence
            )


        #context.abort(grpc.StatusCode.UNIMPLEMENTED, 'ChatAboutItems not Implemented')


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    items_pb2_grpc.add_ItemServiceServicer_to_server(ItemService(), server)

    server.add_insecure_port(f'[::]:{GRPC_PORT}')
    server.start()
    logging.info('%s listening on port %s', SERVICE_NAME,GRPC_PORT)
    server.wait_for_termination()

if __name__ == "__main__":
    serve()