import { Injectable } from '@nestjs/common';
import { PrismaService } from '../../shared/prisma.service';

@Injectable()
export class IncidentsService {
  constructor(private prisma: PrismaService) {}

  async create(dto: { title: string; severity?: number; branchId?: string }) {
    const incident = await this.prisma.incident.create({ data: {
      title: dto.title, severity: dto.severity ?? 3, branchId: dto.branchId || null
    }});
    await this.prisma.incidentEvent.create({ data: {
      incidentId: incident.id, type: 'created', detail: { title: dto.title }
    }});
    return incident;
  }

  byId(id: string) { return this.prisma.incident.findUnique({ where: { id }, include: { timeline: true } }); }

  addEvent(id: string, ev: { type: string; detail: any }) {
    return this.prisma.incidentEvent.create({ data: { incidentId: id, type: ev.type, detail: ev.detail } });
  }
}
