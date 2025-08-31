import { Module } from '@nestjs/common';
import { SlaService } from './sla.service';
import { PrismaService } from '../../shared/prisma.service';

@Module({ providers: [SlaService, PrismaService] })
export class SlaModule {}
