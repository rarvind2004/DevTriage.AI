import { Module } from '@nestjs/common';
import { IncidentsController } from './incidents.controller';
import { IncidentsService } from './incidents.service';
import { PrismaService } from '../../shared/prisma.service';

@Module({
  controllers: [IncidentsController],
  providers: [IncidentsService, PrismaService],
  exports: [IncidentsService]
})
export class IncidentsModule {}
