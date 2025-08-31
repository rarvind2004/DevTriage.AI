import { useState } from 'react'
import axios from 'axios'

export default function Status(){
  const [inc, setInc] = useState<any>(null)
  const [id, setId] = useState('')
  async function load(){
    const r = await axios.get(`${import.meta.env.VITE_API_URL}/incidents/${id}`)
    setInc(r.data)
  }
  return (
    <div className="grid gap-4">
      <div className="flex gap-2">
        <input className="border p-2 rounded" placeholder="Incident id" value={id} onChange={e=>setId(e.target.value)} />
        <button className="bg-black text-white px-3 py-2 rounded" onClick={load}>Load</button>
      </div>
      <pre className="p-4 border rounded-xl overflow-auto">{inc && JSON.stringify(inc, null, 2)}</pre>
    </div>
  )
}
