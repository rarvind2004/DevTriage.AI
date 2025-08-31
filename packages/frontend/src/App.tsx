import { Outlet, Link } from 'react-router-dom'
export default function App(){
  return (
    <div className="min-h-screen grid grid-rows-[auto,1fr]">
      <nav className="p-4 border-b flex gap-4">
        <Link to="/">Dashboard</Link>
        <Link to="/inputs">Inputs</Link>
        <Link to="/status">Status</Link>
        <Link to="/history">History</Link>
        <Link to="/runs">Agent Runs</Link>
      </nav>
      <main className="p-6"><Outlet/></main>
    </div>
  )
}
