import { Module } from '@nestjs/common';
import { PrismaService } from '../shared/prisma.service';
import { IncidentsModule } from './incidents/incidents.module';
import { GatewayModule } from './gateway/gateway.module';
import { AgentModule } from './agent/agent.module';
import { SlaModule } from './sla/sla.module';

@Module({
  imports: [IncidentsModule, GatewayModule, AgentModule, SlaModule],
  providers: [PrismaService],
})
export class AppModule {}
