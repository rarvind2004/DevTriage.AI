import { Body, Controller, Get, Param, Post } from '@nestjs/common';
import { IncidentsService } from './incidents.service';

@Controller('incidents')
export class IncidentsController {
  constructor(private svc: IncidentsService) {}

  @Post()
  create(@Body() dto: { title: string; severity?: number; branchId?: string }) {
    return this.svc.create(dto);
  }

  @Get(':id')
  byId(@Param('id') id: string) { return this.svc.byId(id); }

  @Post(':id/events')
  addEvent(@Param('id') id: string, @Body() body: { type: string; detail: any }) {
    return this.svc.addEvent(id, body);
  }
}
