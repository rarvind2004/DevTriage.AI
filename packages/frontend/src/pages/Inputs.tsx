import { useState } from 'react'
import axios from 'axios'

export default function Inputs(){
  const [title, setTitle] = useState('')
  const [incId, setIncId] = useState('')
  async function createIncident(){
    const res = await axios.post(`${import.meta.env.VITE_API_URL}/incidents`, { title })
    setIncId(res.data.id)
  }
  async function runAgent(){
    await axios.post(`${import.meta.env.VITE_API_URL}/agent/run`, { incidentId: incId, input: title })
    alert('Agent started')
  }
  return (
    <div className="grid gap-4 max-w-xl">
      <input className="border p-2 rounded" placeholder="Alert or log" value={title} onChange={e=>setTitle(e.target.value)} />
      <button className="bg-black text-white px-3 py-2 rounded" onClick={createIncident}>Create Incident</button>
      <button className="bg-indigo-600 text-white px-3 py-2 rounded" onClick={runAgent} disabled={!incId}>Run Agent</button>
      {incId && <div>Incident id: <code>{incId}</code></div>}
    </div>
  )
}
