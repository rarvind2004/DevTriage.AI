import { WebSocketGateway, SubscribeMessage, MessageBody, WebSocketServer } from '@nestjs/websockets';
import { Server } from 'socket.io';

@WebSocketGateway({ cors: { origin: '*' } })
export class EventsGateway {
  @WebSocketServer() server: Server;

  @SubscribeMessage('chat')
  handleChat(@MessageBody() payload: { incidentId: string; content: string }) {
    this.server.to(payload.incidentId).emit('chat', payload);
  }

  @SubscribeMessage('join-room')
  joinRoom(@MessageBody() payload: { incidentId: string }) {
    const room = payload.incidentId;
    this.server.to(room).emit('system', { message: `joined ${room}` });
  }
}
