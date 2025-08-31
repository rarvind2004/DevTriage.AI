import { Body, Controller, Post } from '@nestjs/common';
import axios from 'axios';

@Controller('agent')
export class AgentController {
  @Post('run')
  async run(@Body() body: { incidentId: string; input: string }) {
    const res = await axios.post(process.env.AGENT_URL ?? 'http://agent:8000/run', body);
    return res.data;
  }
}
