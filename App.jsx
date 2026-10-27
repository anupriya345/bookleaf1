import React, { useEffect, useMemo, useState } from 'react';
import { BookOpen, Headphones, LogOut, RefreshCw, Send, Sparkles, Ticket as TicketIcon, ShieldCheck } from 'lucide-react';

const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
const money = n => n == null ? '—' : new Intl.NumberFormat('en-IN',{style:'currency',currency:'INR',maximumFractionDigits:0}).format(n);
const categories = ['Royalty & Payments','ISBN & Metadata Issues','Printing & Quality','Distribution & Availability','Book Status & Production Updates','General Inquiry'];
const statuses = ['Open','In Progress','Resolved','Closed'];
const priorities = ['Critical','High','Medium','Low'];

export default function App(){
 const [token,setToken]=useState(localStorage.getItem('bl_token')||'');
 const [user,setUser]=useState(JSON.parse(localStorage.getItem('bl_user')||'null'));
 const [email,setEmail]=useState('priya.sharma@email.com'), [password,setPassword]=useState('BookLeaf@123');
 const [error,setError]=useState(''), [busy,setBusy]=useState(false);
 const [books,setBooks]=useState([]), [tickets,setTickets]=useState([]), [selected,setSelected]=useState(null);
 const [subject,setSubject]=useState(''), [description,setDescription]=useState(''), [bookId,setBookId]=useState('');
 const [filter,setFilter]=useState('All'), [draft,setDraft]=useState(''), [reply,setReply]=useState(''), [note,setNote]=useState('');
 const [tab,setTab]=useState('tickets');
 const isAdmin=user?.role==='admin';
 const headers=()=>({'Content-Type':'application/json',Authorization:`Bearer ${token}`});
 async function api(path,opts={}){
   const r=await fetch(API+path,{...opts,headers:{...headers(),...(opts.headers||{})}});
   const data=await r.json().catch(()=>({}));
   if(!r.ok) throw new Error(data.detail||`Request failed (${r.status})`);
   return data;
 }
 async function login(e){
   e.preventDefault(); setError('');setBusy(true);
   try{
    const data=await fetch(API+'/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,password})});
    const body=await data.json(); if(!data.ok) throw new Error(body.detail||'Login failed');
    localStorage.setItem('bl_token',body.access_token);localStorage.setItem('bl_user',JSON.stringify(body.user));
    setToken(body.access_token);setUser(body.user);
   }catch(e){setError(e.message)}finally{setBusy(false)}
 }
 function logout(){localStorage.removeItem('bl_token');localStorage.removeItem('bl_user');setToken('');setUser(null);setBooks([]);setTickets([]);setSelected(null)}
 async function load(){
   if(!token)return;
   try{
    const [b,t]=await Promise.all([api('/api/books'),api('/api/tickets')]);
    setBooks(b.items);setTickets(t.items);
    if(selected){const refreshed=t.items.find(x=>x.id===selected.id);setSelected(refreshed||null)}
   }catch(e){setError(e.message)}
 }
 useEffect(()=>{if(token)load()},[token]);
 useEffect(()=>{if(!token)return;const id=setInterval(load,5000);return()=>clearInterval(id)},[token,selected?.id]);
 const visibleTickets=useMemo(()=>tickets.filter(t=>filter==='All'||t.status===filter),[tickets,filter]);
 const totals=useMemo(()=>books.reduce((a,b)=>({sold:a.sold+b.total_copies_sold,earned:a.earned+b.total_royalty_earned,paid:a.paid+b.royalty_paid,pending:a.pending+b.royalty_pending}),{sold:0,earned:0,paid:0,pending:0}),[books]);
 async function createTicket(e){
   e.preventDefault();setError('');
   try{await api('/api/tickets',{method:'POST',body:JSON.stringify({book_id:bookId||null,subject,description})});setSubject('');setDescription('');setBookId('');await load();setTab('tickets')}
   catch(e){setError(e.message)}
 }
 async function selectTicket(t){setSelected(t);setDraft('');setReply('');setNote('')}
 async function updateTicket(patch){
   try{await api(`/api/admin/tickets/${selected.id}`,{method:'PATCH',body:JSON.stringify(patch)});await load()}
   catch(e){setError(e.message)}
 }
 async function generateDraft(){
   try{const d=await api(`/api/admin/tickets/${selected.id}/draft`,{method:'POST',body:'{}'});setDraft(d.draft);setReply(d.draft)}
   catch(e){setError(e.message)}
 }
 async function sendReply(e){
   e.preventDefault();if(!reply.trim())return;
   try{await api(`/api/admin/tickets/${selected.id}/messages`,{method:'POST',body:JSON.stringify({message:reply})});setReply('');await load()}
   catch(e){setError(e.message)}
 }
 async function addNote(e){
   e.preventDefault();if(!note.trim())return;
   try{await api(`/api/admin/tickets/${selected.id}/notes`,{method:'POST',body:JSON.stringify({note})});setNote('');await load()}
   catch(e){setError(e.message)}
 }
 if(!token||!user) return <main className="login-wrap"><form className="login-card" onSubmit={login}>
   <div className="brand"><span className="brand-icon"><BookOpen/></span><div><h1>BookLeaf</h1><p>Author Support Portal</p></div></div>
   <h2>Welcome back</h2><p className="muted">Sign in to manage books and support requests.</p>
   {error&&<div className="error">{error}</div>}
   <label>Email address<input type="email" value={email} onChange={e=>setEmail(e.target.value)} required/></label>
   <label>Password<input type="password" value={password} onChange={e=>setPassword(e.target.value)} required/></label>
   <button className="primary full" disabled={busy}>{busy?'Signing in…':'Sign in'}</button>
   <div className="demo"><b>Demo accounts</b><br/>Author: priya.sharma@email.com<br/>Admin: admin@bookleaf.local<br/>Password: BookLeaf@123</div>
 </form></main>;

 return <div className="app-shell">
  <aside className="sidebar">
   <div className="brand"><span className="brand-icon"><BookOpen/></span><div><h1>BookLeaf</h1><p>Support workspace</p></div></div>
   <div className="user-chip"><div className="avatar">{user.name?.slice(0,1)}</div><div><b>{user.name}</b><small>{isAdmin?'Administrator':'Author account'}</small></div></div>
   <nav>
    <button className={tab==='tickets'?'nav-active':''} onClick={()=>setTab('tickets')}><TicketIcon size={18}/> {isAdmin?'Ticket queue':'My tickets'}</button>
    {!isAdmin&&<button className={tab==='books'?'nav-active':''} onClick={()=>setTab('books')}><BookOpen size={18}/> My books</button>}
    {!isAdmin&&<button className={tab==='new'?'nav-active':''} onClick={()=>setTab('new')}><Send size={18}/> New support query</button>}
   </nav>
   <div className="sidebar-bottom"><div className="secure"><ShieldCheck size={17}/> Secure workspace</div><button className="logout" onClick={logout}><LogOut size={17}/> Sign out</button></div>
  </aside>
  <main className="main">
   <header className="topbar"><div><p className="eyebrow">{isAdmin?'OPERATIONS':'AUTHOR WORKSPACE'}</p><h2>{isAdmin?'Support operations':`Hello, ${user.name.split(' ')[0]}`}</h2></div><button className="icon-button" onClick={load} title="Refresh"><RefreshCw size={18}/></button></header>
   {error&&<div className="error dismiss"><span>{error}</span><button onClick={()=>setError('')}>×</button></div>}
   {!isAdmin&&<section className="stats">
    <Stat label="Books sold" value={totals.sold.toLocaleString('en-IN')} icon={<BookOpen/>}/>
    <Stat label="Royalty earned" value={money(totals.earned)} icon={<Sparkles/>}/>
    <Stat label="Royalty paid" value={money(totals.paid)} icon={<ShieldCheck/>}/>
    <Stat label="Royalty pending" value={money(totals.pending)} icon={<Headphones/>}/>
   </section>}
   {tab==='books'&&!isAdmin&&<section className="panel"><div className="panel-heading"><div><h3>My books</h3><p>Publication, sales and royalty information</p></div></div><div className="table-wrap"><table><thead><tr><th>Book</th><th>Status</th><th>Copies sold</th><th>Earned</th><th>Paid</th><th>Pending</th></tr></thead><tbody>{books.map(b=><tr key={b.book_id}><td><b>{b.title}</b><small>{b.book_id} · {b.isbn}</small></td><td><span className="pill">{b.status}</span></td><td>{b.total_copies_sold}</td><td>{money(b.total_royalty_earned)}</td><td>{money(b.royalty_paid)}</td><td>{money(b.royalty_pending)}</td></tr>)}</tbody></table></div></section>}
   {tab==='new'&&!isAdmin&&<section className="panel form-panel"><div className="panel-heading"><div><h3>Submit a support query</h3><p>Tell us what you need help with.</p></div></div><form onSubmit={createTicket} className="stack-form">
    <label>Book<select value={bookId} onChange={e=>setBookId(e.target.value)}><option value="">General / Account Level</option>{books.map(b=><option key={b.book_id} value={b.book_id}>{b.title}</option>)}</select></label>
    <label>Subject<input value={subject} onChange={e=>setSubject(e.target.value)} minLength="3" required placeholder="Briefly describe your issue"/></label>
    <label>Detailed description<textarea value={description} onChange={e=>setDescription(e.target.value)} minLength="10" required rows="6" placeholder="Include relevant details so our team can help…"/></label>
    <p className="muted small">File attachment UI can be added; actual upload is optional in the assignment.</p><button className="primary"><Send size={16}/> Submit ticket</button>
   </form></section>}
   {tab==='tickets'&&<div className="ticket-layout">
    <section className="panel ticket-list"><div className="panel-heading"><div><h3>{isAdmin?'All support tickets':'My tickets'}</h3><p>{tickets.length} total · refreshes automatically</p></div><select className="filter" value={filter} onChange={e=>setFilter(e.target.value)}><option>All</option>{statuses.map(s=><option key={s}>{s}</option>)}</select></div>
     {visibleTickets.length===0?<div className="empty"><TicketIcon size={28}/><b>No tickets yet</b><p>Support conversations will appear here.</p></div>:visibleTickets.map(t=><button key={t.id} className={`ticket-row ${selected?.id===t.id?'ticket-selected':''}`} onClick={()=>selectTicket(t)}>
      <div className="ticket-row-top"><span className={`priority p-${t.priority.toLowerCase()}`}>{t.priority}</span><small>#{t.id}</small></div><b>{t.subject}</b><p>{isAdmin?`${t.author_name} · `:''}{t.book_title}</p><div className="ticket-row-bottom"><span className="pill">{t.status}</span><small>{new Date(t.created_at).toLocaleDateString()}</small></div>
     </button>)}
    </section>
    <section className="panel detail-panel">
     {!selected?<div className="empty detail-empty"><TicketIcon size={32}/><b>Select a ticket</b><p>Choose a conversation to view details.</p></div>:<div className="detail-content">
      <div className="panel-heading"><div><span className="eyebrow">TICKET #{selected.id}</span><h3>{selected.subject}</h3><p>{selected.author_name} · {selected.book_title}</p></div><span className="pill">{selected.status}</span></div>
      <div className="query-card"><b>Original query</b><p>{selected.description}</p></div>
      {isAdmin&&<div className="admin-controls">
       <label>Category<select value={selected.category} onChange={e=>updateTicket({category:e.target.value})}>{categories.map(c=><option key={c}>{c}</option>)}</select></label>
       <label>Priority<select value={selected.priority} onChange={e=>updateTicket({priority:e.target.value})}>{priorities.map(p=><option key={p}>{p}</option>)}</select></label>
       <label>Status<select value={selected.status} onChange={e=>updateTicket({status:e.target.value})}>{statuses.map(s=><option key={s}>{s}</option>)}</select></label>
      </div>}
      <div className="conversation"><h4>Conversation</h4>{selected.messages?.length===0&&<p className="muted small">No replies yet.</p>}{selected.messages?.map(m=><div className={`message ${m.sender_user_id===selected.author_user_id?'from-author':'from-admin'}`} key={m.id}><small>{m.sender_name} · {new Date(m.created_at).toLocaleString()}</small><p>{m.message}</p></div>)}</div>
      {isAdmin&&<div className="reply-area">
       <div className="section-line"><h4>AI-assisted reply</h4><button className="secondary" onClick={generateDraft}><Sparkles size={15}/> Generate draft</button></div>
       <form onSubmit={sendReply}><textarea rows="5" value={reply} onChange={e=>setReply(e.target.value)} placeholder="Generate or write a response, then send…" required/><button className="primary"><Send size={16}/> Send response</button></form>
       <form onSubmit={addNote} className="note-form"><label>Internal note (admin only)<textarea rows="2" value={note} onChange={e=>setNote(e.target.value)} placeholder="Private note not visible to author"/></label><button className="secondary">Add note</button></form>
       {selected.internal_notes?.length>0&&<div className="notes"><b>Private notes</b>{selected.internal_notes.map(n=><p key={n.id}>{n.note}</p>)}</div>}
      </div>}
     </div>}
    </section>
   </div>}
   <footer>BookLeaf Publishing · Author Support & Communication Portal <span>Confidential demo</span></footer>
  </main>
 </div>
}
function Stat({label,value,icon}){return <div className="stat"><div className="stat-top"><span>{label}</span><span className="stat-icon">{icon}</span></div><strong>{value}</strong></div>}
