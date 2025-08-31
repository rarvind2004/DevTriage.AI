import { Module } from '@nestjs/common';
import { AgentController } from './agent.controller';
import { PrismaService } from '../../shared/prisma.service';

@Module({ controllers: [AgentController], providers: [PrismaService] })
export class AgentModule {}
