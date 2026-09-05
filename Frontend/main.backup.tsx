import 'styles.css';

type Page = 'register' | 'dashboard' | 'contacts' | 'products';
type RecordItem = { id: number; name: string; email?: string; company: string; phone?: string; status: 'Active' | 'Archived'; amount?: string; sku?: string; stock?: number };

const initialContacts: RecordItem[] = [
  { id: 1, name: 'Aarav Mehta', email: 'aarav@northstar.co', company: 'Northstar Labs', phone: '+91 98765 21043', status: 'Active', amount: '₹ 48,750' },
  { id: 2, name: 'Priya Kapoor', email: 'priya@atelier.in', company: 'Atelier House', phone: '+91 99651 20476', status: 'Active', amount: '₹ 27,100' },
  { id: 3, name: 'Kabir Shah', email: 'kabir@meridian.com', company: 'Meridian & Co.', phone: '+91 99884 18231', status: 'Active', amount: '₹ 15,600' },
  { id: 4, name: 'Diya Nair', email: 'diya@verve.studio', company: 'Verve Studio', phone: '+91 98220 12131', status: 'Archived', amount: '₹ 0' },
  { id: 5, name: 'Rohan Das', email: 'rohan@atlas.io', company: 'Atlas Systems', phone: '+91 97970 65311', status: 'Active', amount: '₹ 84,920' },
];
const initialProducts: RecordItem[] = [
  { id: 1, name: 'Accounting consultation', company: 'Professional services', sku: 'SERV-001', stock: 99, status: 'Active', amount: '₹ 4,500' },
  { id: 2, name: 'Growth plan', company: 'Subscription', sku: 'SUB-204', stock: 42, status: 'Active', amount: '₹ 2,999' },
  { id: 3, name: 'Ledger migration', company: 'Professional services', sku: 'SERV-014', stock: 12, status: 'Active', amount: '₹ 12,000' },
  { id: 4, name: 'Tax filing add-on', company: 'Subscription', sku: 'ADD-106', stock: 0, status: 'Archived', amount: '₹ 1,499' },
];

const nav = [{ label: 'Dashboard', icon: LayoutDashboard, page: 'dashboard' }, { label: 'Sales', icon: CircleDollarSign }, { label: 'Purchase', icon: ShoppingBag }, { label: 'Account', icon: ClipboardList, page: 'contacts' }, { label: 'Reports', icon: BarChart3 }];

function App() {
  const [page, setPage] = useState<Page>('register');
  const [contacts, setContacts] = useState(initialContacts);
  const [products, setProducts] = useState(initialProducts);
  const [query, setQuery] = useState('');
  const [modal, setModal] = useState<{ kind: 'contact' | 'product'; item?: RecordItem } | null>(null);
  const [toast, setToast] = useState('');
  const activeList = page === 'products' ? products : contacts;
  const filtered = useMemo(() => activeList.filter(x => `${x.name} ${x.company} ${x.status}`.toLowerCase().includes(query.toLowerCase())), [activeList, query]);
  const isList = page === 'contacts' || page === 'products';

  function flash(message: string) { setToast(message); window.setTimeout(() => setToast(''), 2500); }
  function saveRecord(data: RecordItem) {
    const set = modal?.kind === 'product' ? setProducts : setContacts;
    set(current => current.some(x => x.id === data.id) ? current.map(x => x.id === data.id ? data : x) : [...current, data]);
    setModal(null); flash(data.id > 10 ? 'New record created' : 'Changes saved');
  }
  function archive(item: RecordItem) {
    const set = page === 'products' ? setProducts : setContacts;
    set(current => current.map(x => x.id === item.id ? { ...x, status: x.status === 'Active' ? 'Archived' : 'Active' } : x));
    flash(`${item.name} ${item.status === 'Active' ? 'archived' : 'restored'}`);
  }

  if (page === 'register') return <Register onAdmin={() => setPage('dashboard')} />;
  return <div className="app-shell">
    <aside className="sidebar"><div className="brand"><div className="brand-mark">L</div><span>ledgerly</span></div><div className="workspace"><span className="dot"/>Acme Finance <ChevronDown size={15}/></div>
      <nav>{nav.map(({label, icon: Icon, page: navPage}) => <button key={label} className={(page === navPage || (label === 'Account' && page === 'products')) ? 'nav-item active' : 'nav-item'} onClick={() => navPage && setPage(navPage as Page)}><Icon size={18}/><span>{label}</span>{label === 'Account' && <ChevronDown size={14} className="nav-chevron"/>}</button>)}
        {(page === 'contacts' || page === 'products') && <div className="subnav"><button className={page === 'contacts' ? 'selected' : ''} onClick={() => setPage('contacts')}><Users size={15}/>Contacts</button><button className={page === 'products' ? 'selected' : ''} onClick={() => setPage('products')}><Package size={15}/>Products</button></div>}
      </nav><div className="sidebar-bottom"><button className="help-card"><span>Need a hand?</span><small>View help center</small><ArrowRight size={16}/></button><div className="profile"><div className="avatar">AM</div><div><b>Aarav Mehta</b><small>Administrator</small></div><MoreHorizontal size={18}/></div></div>
    </aside>
    <main><header className="topbar"><button className="mobile-menu"><Menu size={20}/></button><div className="global-search"><Search size={18}/><input placeholder="Search anything..."/></div><div className="top-actions"><button><Bell size={19}/><i/></button><div className="avatar">AM</div></div></header>
      {page === 'dashboard' && <Dashboard onAccount={() => setPage('contacts')} />}
      {isList && <ListPage type={page === 'products' ? 'product' : 'contact'} rows={filtered} query={query} onQuery={setQuery} onAdd={() => setModal({kind: page === 'products' ? 'product' : 'contact'})} onEdit={item => setModal({kind: page === 'products' ? 'product' : 'contact', item})} onArchive={archive}/>} 
    </main>
    {modal && <RecordModal type={modal.kind} item={modal.item} onClose={() => setModal(null)} onSave={saveRecord}/>} {toast && <div className="toast">{toast}</div>}
  </div>;
}

function Register({onAdmin}: {onAdmin: () => void}) { const [mode, setMode] = useState<'user' | 'admin'>('admin'); return <div className="register-page"><div className="register-art"><div className="brand"><div className="brand-mark">L</div>ledgerly</div><div><p className="eyebrow">SMARTER ACCOUNTING, MADE SIMPLE</p><h1>Every number.<br/><em>One clear view.</em></h1><p>Run your finances, sales and operations from a beautifully simple workspace.</p></div><div className="art-card"><span>Sep 2025</span><b>₹ 4,28,540</b><small>+18.4% from last month</small><div className="chart"><i/><i/><i/><i/><i/><i/><i/></div></div></div><section className="register-card"><div className="form-head"><span className="eyebrow">WELCOME TO LEDGERLY</span><h2>Create your workspace</h2><p>Choose how you’ll use Ledgerly to get started.</p></div><div className="mode-switch"><button className={mode === 'user' ? 'mode selected' : 'mode'} onClick={() => setMode('user')}><Users/><span><b>User mode</b><small>Manage your own account</small></span></button><button className={mode === 'admin' ? 'mode selected' : 'mode'} onClick={() => setMode('admin')}><Boxes/><span><b>Admin mode</b><small>Run your organization</small></span></button></div><label>Work email<input type="email" placeholder="you@company.com" /></label><label>Password<input type="password" placeholder="Create a strong password" /></label><button className="primary" onClick={onAdmin}>Create {mode === 'admin' ? 'admin' : 'user'} account <ArrowRight size={18}/></button><p className="signin">Already have an account? <a>Sign in</a></p></section></div> }

function Dashboard({onAccount}: {onAccount: () => void}) { const modules = [{title:'Sales', detail:'Invoices, customers & payments', icon:CircleDollarSign, tone:'orange'}, {title:'Purchase', detail:'Bills, vendors & expenses', icon:ShoppingBag, tone:'purple'}, {title:'Account', detail:'Contacts, products & ledger', icon:ClipboardList, tone:'blue', action:onAccount}, {title:'Reports', detail:'Insights & financial health', icon:BarChart3, tone:'green'}]; return <div className="page dashboard"><div className="page-heading"><div><span className="eyebrow">OVERVIEW</span><h1>Good morning, Aarav <span>✦</span></h1><p>Here’s what’s happening with your business today.</p></div><button className="primary compact"><Plus size={17}/>New transaction</button></div><div className="stat-grid"><Stat label="Total balance" value="₹ 4,28,540" change="↑ 18.4%"/><Stat label="Money in" value="₹ 1,84,200" change="↑ 12.8%"/><Stat label="Money out" value="₹ 86,480" change="↓ 4.3%"/><Stat label="Outstanding" value="₹ 32,750" change="7 invoices"/></div><section className="chart-panel"><div><h3>Cash flow</h3><p>Income and expenses over time</p></div><div className="legend"><i className="income"/>Income <i className="expense"/>Expenses</div><div className="line-chart"><svg viewBox="0 0 720 180" preserveAspectRatio="none"><path d="M0 145 C55 128 80 143 120 105 S190 128 230 92 S295 110 340 61 S410 96 456 55 S530 70 570 38 S640 58 720 12" fill="none" stroke="#6e72dd" strokeWidth="4"/><path d="M0 156 C56 138 83 158 120 134 S190 149 230 126 S292 145 340 117 S405 132 456 106 S520 128 570 95 S642 117 720 82" fill="none" stroke="#e9a766" strokeWidth="3"/></svg></div><div className="months"><span>Apr</span><span>May</span><span>Jun</span><span>Jul</span><span>Aug</span><span>Sep</span></div></section><section><div className="section-title"><div><h2>Business workspace</h2><p>Choose an area to continue working</p></div></div><div className="module-grid">{modules.map(({title,detail,icon:Icon,tone,action}) => <button className="module-card" onClick={action} key={title}><div className={`module-icon ${tone}`}><Icon size={22}/></div><div><h3>{title}</h3><p>{detail}</p></div><ArrowRight size={18}/></button>)}</div></section></div> }
function Stat({label,value,change}:{label:string,value:string,change:string}) { return <article className="stat"><span>{label}</span><strong>{value}</strong><small className={change.includes('↓') ? 'down' : ''}>{change}</small></article> }
function ListPage({type,rows,query,onQuery,onAdd,onEdit,onArchive}: {type:'contact'|'product';rows:RecordItem[];query:string;onQuery:(q:string)=>void;onAdd:()=>void;onEdit:(x:RecordItem)=>void;onArchive:(x:RecordItem)=>void}) { const isProduct=type==='product'; return <div className="page list-page"><div className="breadcrumb">Account <span>/</span> {isProduct ? 'Products' : 'Contacts'}</div><div className="list-heading"><div><h1>{isProduct ? 'Products' : 'Contacts'}</h1><p>{isProduct ? 'Manage items and services you sell.' : 'People and companies you do business with.'}</p></div><button className="primary compact" onClick={onAdd}><Plus size={17}/>Add {type}</button></div><div className="table-panel"><div className="table-tools"><div className="table-search"><Search size={17}/><input value={query} onChange={e=>onQuery(e.target.value)} placeholder={`Search ${isProduct ? 'products' : 'contacts'}...`}/></div><button className="filter">Filter <ChevronDown size={15}/></button></div><div className="count">{rows.length} {isProduct ? 'products' : 'contacts'}</div><div className="data-table"><div className="table-row table-head"><span>{isProduct?'PRODUCT':'CONTACT'}</span><span>{isProduct?'CATEGORY':'COMPANY'}</span><span>{isProduct?'SKU':'EMAIL'}</span><span>{isProduct?'IN STOCK':'PHONE'}</span><span>{isProduct?'PRICE':'OPEN BALANCE'}</span><span>STATUS</span><span/></div>{rows.map(row => <div className="table-row" key={row.id}><span className="name-cell"><div className="initial">{row.name.split(' ').map(x=>x[0]).slice(0,2).join('')}</div><b>{row.name}</b></span><span>{row.company}</span><span>{isProduct?row.sku:row.email}</span><span>{isProduct?`${row.stock} units`:row.phone}</span><span>{row.amount}</span><span><i className={`status ${row.status.toLowerCase()}`}/>{row.status}</span><span className="row-actions"><button title="Edit" onClick={()=>onEdit(row)}><Pencil size={16}/></button><button title="Archive" onClick={()=>onArchive(row)}><Archive size={16}/></button></span></div>)}</div></div></div> }
function RecordModal({type,item,onClose,onSave}:{type:'contact'|'product';item?:RecordItem;onClose:()=>void;onSave:(x:RecordItem)=>void}) { const product=type==='product'; const [name,setName]=useState(item?.name||''); const [company,setCompany]=useState(item?.company||''); const [email,setEmail]=useState(item?.email||''); const [phone,setPhone]=useState(item?.phone||''); const [amount,setAmount]=useState(item?.amount||''); function submit(e:React.FormEvent){e.preventDefault(); onSave(product?{id:item?.id||Date.now(),name,company,sku:item?.sku||'NEW-001',stock:item?.stock||0,status:item?.status||'Active',amount}:{id:item?.id||Date.now(),name,company,email,phone,status:item?.status||'Active',amount});} return <div className="modal-backdrop"><form className="modal" onSubmit={submit}><button type="button" className="close" onClick={onClose}><X/></button><span className="eyebrow">ACCOUNT / {product?'PRODUCTS':'CONTACTS'}</span><h2>{item?'Edit':'Create'} {type}</h2><p>Add the details you need to keep your records accurate.</p><label>{product?'Product name':'Full name'}<input autoFocus required value={name} onChange={e=>setName(e.target.value)} placeholder={product?'e.g. Consulting package':'e.g. Priya Kapoor'}/></label><label>{product?'Category':'Company'}<input required value={company} onChange={e=>setCompany(e.target.value)} placeholder={product?'Services':'Company name'}/></label>{!product&&<><label>Email<input required type="email" value={email} onChange={e=>setEmail(e.target.value)} placeholder="name@company.com"/></label><label>Phone<input value={phone} onChange={e=>setPhone(e.target.value)} placeholder="+91 00000 00000"/></label></>}<label>{product?'Price':'Opening balance'}<input value={amount} onChange={e=>setAmount(e.target.value)} placeholder="₹ 0"/></label><div className="modal-actions"><button type="button" className="secondary" onClick={onClose}>Cancel</button><button className="primary">{item?'Save changes':'Create '+type}</button></div></form></div> }
export default App;
outputs/accounting-admin-dashboard/src/main.tsx
import { useMemo, useState } from 'react';
import { Archive, ArrowRight, BarChart3, Bell, Boxes, ChevronDown, CircleDollarSign, ClipboardList, FileText, LayoutDashboard, Menu, MoreHorizontal, Package, Pencil, Plus, Search, ShoppingBag, Users, X } from 'lucide-react';
import './styles.css';

type Page = 'register' | 'dashboard' | 'contacts' | 'products';
type RecordItem = { id: number; name: string; email?: string; company: string; phone?: string; status: 'Active' | 'Archived'; amount?: string; sku?: string; stock?: number };

const initialContacts: RecordItem[] = [
  { id: 1, name: 'Aarav Mehta', email: 'aarav@northstar.co', company: 'Northstar Labs', phone: '+91 98765 21043', status: 'Active', amount: '₹ 48,750' },
  { id: 2, name: 'Priya Kapoor', email: 'priya@atelier.in', company: 'Atelier House', phone: '+91 99651 20476', status: 'Active', amount: '₹ 27,100' },
  { id: 3, name: 'Kabir Shah', email: 'kabir@meridian.com', company: 'Meridian & Co.', phone: '+91 99884 18231', status: 'Active', amount: '₹ 15,600' },
  { id: 4, name: 'Diya Nair', email: 'diya@verve.studio', company: 'Verve Studio', phone: '+91 98220 12131', status: 'Archived', amount: '₹ 0' },
  { id: 5, name: 'Rohan Das', email: 'rohan@atlas.io', company: 'Atlas Systems', phone: '+91 97970 65311', status: 'Active', amount: '₹ 84,920' },
];
const initialProducts: RecordItem[] = [
  { id: 1, name: 'Accounting consultation', company: 'Professional services', sku: 'SERV-001', stock: 99, status: 'Active', amount: '₹ 4,500' },
  { id: 2, name: 'Growth plan', company: 'Subscription', sku: 'SUB-204', stock: 42, status: 'Active', amount: '₹ 2,999' },
  { id: 3, name: 'Ledger migration', company: 'Professional services', sku: 'SERV-014', stock: 12, status: 'Active', amount: '₹ 12,000' },
  { id: 4, name: 'Tax filing add-on', company: 'Subscription', sku: 'ADD-106', stock: 0, status: 'Archived', amount: '₹ 1,499' },
];

const nav = [{ label: 'Dashboard', icon: LayoutDashboard, page: 'dashboard' }, { label: 'Sales', icon: CircleDollarSign }, { label: 'Purchase', icon: ShoppingBag }, { label: 'Account', icon: ClipboardList, page: 'contacts' }, { label: 'Reports', icon: BarChart3 }];

function App() {
  const [page, setPage] = useState<Page>('register');
  const [contacts, setContacts] = useState(initialContacts);
  const [products, setProducts] = useState(initialProducts);
  const [query, setQuery] = useState('');
  const [modal, setModal] = useState<{ kind: 'contact' | 'product'; item?: RecordItem } | null>(null);
  const [toast, setToast] = useState('');
  const activeList = page === 'products' ? products : contacts;
  const filtered = useMemo(() => activeList.filter(x => `${x.name} ${x.company} ${x.status}`.toLowerCase().includes(query.toLowerCase())), [activeList, query]);
  const isList = page === 'contacts' || page === 'products';

  function flash(message: string) { setToast(message); window.setTimeout(() => setToast(''), 2500); }
  function saveRecord(data: RecordItem) {
    const set = modal?.kind === 'product' ? setProducts : setContacts;
    set(current => current.some(x => x.id === data.id) ? current.map(x => x.id === data.id ? data : x) : [...current, data]);
    setModal(null); flash(data.id > 10 ? 'New record created' : 'Changes saved');
  }
  function archive(item: RecordItem) {
    const set = page === 'products' ? setProducts : setContacts;
    set(current => current.map(x => x.id === item.id ? { ...x, status: x.status === 'Active' ? 'Archived' : 'Active' } : x));
    flash(`${item.name} ${item.status === 'Active' ? 'archived' : 'restored'}`);
  }

  if (page === 'register') return <Register onAdmin={() => setPage('dashboard')} />;
  return <div className="app-shell">
    <aside className="sidebar"><div className="brand"><div className="brand-mark">L</div><span>ledgerly</span></div><div className="workspace"><span className="dot"/>Acme Finance <ChevronDown size={15}/></div>
      <nav>{nav.map(({label, icon: Icon, page: navPage}) => <button key={label} className={(page === navPage || (label === 'Account' && page === 'products')) ? 'nav-item active' : 'nav-item'} onClick={() => navPage && setPage(navPage as Page)}><Icon size={18}/><span>{label}</span>{label === 'Account' && <ChevronDown size={14} className="nav-chevron"/>}</button>)}
        {(page === 'contacts' || page === 'products') && <div className="subnav"><button className={page === 'contacts' ? 'selected' : ''} onClick={() => setPage('contacts')}><Users size={15}/>Contacts</button><button className={page === 'products' ? 'selected' : ''} onClick={() => setPage('products')}><Package size={15}/>Products</button></div>}
      </nav><div className="sidebar-bottom"><button className="help-card"><span>Need a hand?</span><small>View help center</small><ArrowRight size={16}/></button><div className="profile"><div className="avatar">AM</div><div><b>Aarav Mehta</b><small>Administrator</small></div><MoreHorizontal size={18}/></div></div>
    </aside>
    <main><header className="topbar"><button className="mobile-menu"><Menu size={20}/></button><div className="global-search"><Search size={18}/><input placeholder="Search anything..."/></div><div className="top-actions"><button><Bell size={19}/><i/></button><div className="avatar">AM</div></div></header>
      {page === 'dashboard' && <Dashboard onAccount={() => setPage('contacts')} />}
      {isList && <ListPage type={page === 'products' ? 'product' : 'contact'} rows={filtered} query={query} onQuery={setQuery} onAdd={() => setModal({kind: page === 'products' ? 'product' : 'contact'})} onEdit={item => setModal({kind: page === 'products' ? 'product' : 'contact', item})} onArchive={archive}/>} 
    </main>
    {modal && <RecordModal type={modal.kind} item={modal.item} onClose={() => setModal(null)} onSave={saveRecord}/>} {toast && <div className="toast">{toast}</div>}
  </div>;
}

function Register({onAdmin}: {onAdmin: () => void}) { const [mode, setMode] = useState<'user' | 'admin'>('admin'); return <div className="register-page"><div className="register-art"><div className="brand"><div className="brand-mark">L</div>ledgerly</div><div><p className="eyebrow">SMARTER ACCOUNTING, MADE SIMPLE</p><h1>Every number.<br/><em>One clear view.</em></h1><p>Run your finances, sales and operations from a beautifully simple workspace.</p></div><div className="art-card"><span>Sep 2025</span><b>₹ 4,28,540</b><small>+18.4% from last month</small><div className="chart"><i/><i/><i/><i/><i/><i/><i/></div></div></div><section className="register-card"><div className="form-head"><span className="eyebrow">WELCOME TO LEDGERLY</span><h2>Create your workspace</h2><p>Choose how you’ll use Ledgerly to get started.</p></div><div className="mode-switch"><button className={mode === 'user' ? 'mode selected' : 'mode'} onClick={() => setMode('user')}><Users/><span><b>User mode</b><small>Manage your own account</small></span></button><button className={mode === 'admin' ? 'mode selected' : 'mode'} onClick={() => setMode('admin')}><Boxes/><span><b>Admin mode</b><small>Run your organization</small></span></button></div><label>Work email<input type="email" placeholder="you@company.com" /></label><label>Password<input type="password" placeholder="Create a strong password" /></label><button className="primary" onClick={onAdmin}>Create {mode === 'admin' ? 'admin' : 'user'} account <ArrowRight size={18}/></button><p className="signin">Already have an account? <a>Sign in</a></p></section></div> }

function Dashboard({onAccount}: {onAccount: () => void}) { const modules = [{title:'Sales', detail:'Invoices, customers & payments', icon:CircleDollarSign, tone:'orange'}, {title:'Purchase', detail:'Bills, vendors & expenses', icon:ShoppingBag, tone:'purple'}, {title:'Account', detail:'Contacts, products & ledger', icon:ClipboardList, tone:'blue', action:onAccount}, {title:'Reports', detail:'Insights & financial health', icon:BarChart3, tone:'green'}]; return <div className="page dashboard"><div className="page-heading"><div><span className="eyebrow">OVERVIEW</span><h1>Good morning, Aarav <span>✦</span></h1><p>Here’s what’s happening with your business today.</p></div><button className="primary compact"><Plus size={17}/>New transaction</button></div><div className="stat-grid"><Stat label="Total balance" value="₹ 4,28,540" change="↑ 18.4%"/><Stat label="Money in" value="₹ 1,84,200" change="↑ 12.8%"/><Stat label="Money out" value="₹ 86,480" change="↓ 4.3%"/><Stat label="Outstanding" value="₹ 32,750" change="7 invoices"/></div><section className="chart-panel"><div><h3>Cash flow</h3><p>Income and expenses over time</p></div><div className="legend"><i className="income"/>Income <i className="expense"/>Expenses</div><div className="line-chart"><svg viewBox="0 0 720 180" preserveAspectRatio="none"><path d="M0 145 C55 128 80 143 120 105 S190 128 230 92 S295 110 340 61 S410 96 456 55 S530 70 570 38 S640 58 720 12" fill="none" stroke="#6e72dd" strokeWidth="4"/><path d="M0 156 C56 138 83 158 120 134 S190 149 230 126 S292 145 340 117 S405 132 456 106 S520 128 570 95 S642 117 720 82" fill="none" stroke="#e9a766" strokeWidth="3"/></svg></div><div className="months"><span>Apr</span><span>May</span><span>Jun</span><span>Jul</span><span>Aug</span><span>Sep</span></div></section><section><div className="section-title"><div><h2>Business workspace</h2><p>Choose an area to continue working</p></div></div><div className="module-grid">{modules.map(({title,detail,icon:Icon,tone,action}) => <button className="module-card" onClick={action} key={title}><div className={`module-icon ${tone}`}><Icon size={22}/></div><div><h3>{title}</h3><p>{detail}</p></div><ArrowRight size={18}/></button>)}</div></section></div> }