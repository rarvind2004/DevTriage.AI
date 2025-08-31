import { Injectable, OnModuleInit } from '@nestjs/common';
import { PrismaService } from '../../shared/prisma.service';
import { Kafka, logLevel } from 'kafkajs';

@Injectable()
export class SlaService implements OnModuleInit {
  private producer = new Kafka({ clientId: process.env.KAFKA_CLIENT_ID!, brokers: [process.env.KAFKA_BROKER!], logLevel: logLevel.ERROR }).producer();

  constructor(private prisma: PrismaService) {}

  async onModuleInit() {
    await this.producer.connect();
    // tiny loop for MVP, in production use pg_cron or listen notify
    setInterval(() => this.tick(), 5_000);
  }

  private async tick() {
    const due = await this.prisma.sLATimer.findMany({ where: { fired: false, deadline: { lte: new Date() } } });
    for (const t of due) {
      await this.prisma.sLATimer.update({ where: { id: t.id }, data: { fired: true } });
      await this.producer.send({ topic: 'sla.events', messages: [{ value: JSON.stringify({ incidentId: t.incidentId, kind: t.kind }) }] });
    }
  }
}
