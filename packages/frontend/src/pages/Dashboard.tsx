import { useEffect, useState } from 'react'
import { LineChart, Line, CartesianGrid, XAxis, YAxis, Tooltip } from 'recharts'

export default function Dashboard(){
  const [metrics, setMetrics] = useState<{x:string, mttr:number}[]>([])
  useEffect(()=>{ setMetrics([
    { x: 'Mon', mttr: 42 }, { x: 'Tue', mttr: 35 }, { x: 'Wed', mttr: 28 }, { x: 'Thu', mttr: 31 }, { x: 'Fri', mttr: 25 }
  ]) }, [])

  return (
    <div className="grid gap-6">
      <h1 className="text-2xl font-semibold">Analytics</h1>
      <div className="p-4 border rounded-xl">
        <LineChart width={720} height={320} data={metrics}>
          <Line type="monotone" dataKey="mttr" />
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="x" /><YAxis /><Tooltip />
        </LineChart>
      </div>
    </div>
  )
}
