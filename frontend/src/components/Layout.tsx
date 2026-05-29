import React from 'react';
import { Link, useLocation, Outlet } from 'react-router-dom';
import { Home as HomeIcon, FileText, CreditCard, ChevronRight, FileSpreadsheet } from 'lucide-react';

const Layout: React.FC = () => {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Início', icon: HomeIcon },
    { path: '/ip', label: 'Importação IP', icon: FileText },
    { path: '/genial', label: 'Extrato Genial', icon: CreditCard },
    { path: '/excel-to-csv', label: 'Excel para CSV', icon: FileSpreadsheet },
  ];

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      {/* Sidebar - Deep Navy Gradient */}
      <aside className="w-64 bg-gradient-to-b from-primary to-primary-container text-white flex flex-col shadow-2xl z-20">
        <div className="p-6 border-b border-white/10">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-secondary rounded-lg flex items-center justify-center font-bold text-lg">C</div>
            <div>
              <h1 className="text-sm font-black tracking-widest leading-none">CONTABIL ALONG</h1>
              <span className="text-[10px] text-secondary-container font-semibold uppercase tracking-tighter">Finance Hub</span>
            </div>
          </div>
        </div>

        <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
          <p className="text-[10px] font-bold text-white/40 uppercase tracking-[0.2em] px-2 mb-4">Navegação Principal</p>
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            const Icon = item.icon;
            
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`
                  flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-semibold transition-all duration-200
                  ${isActive 
                    ? 'bg-white/10 text-white border-l-4 border-secondary-container shadow-lg translate-x-1' 
                    : 'text-white/70 hover:bg-white/5 hover:text-white hover:translate-x-1'}
                `}
              >
                <Icon size={18} className={isActive ? 'text-secondary-container' : ''} />
                {item.label}
              </Link>
            );
          })}
        </nav>

      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
        {/* Topbar */}
        <header className="h-16 bg-surface border-b border-outline-variant flex items-center justify-between px-8 z-10">
          <div className="flex items-center gap-2 text-xs font-medium text-slate-400">
            <span>Sistema</span>
            <ChevronRight size={14} />
            <span className="text-primary font-bold">
              {navItems.find(i => i.path === location.pathname)?.label || 'Painel'}
            </span>
          </div>

        </header>

        {/* Dynamic Page Content */}
        <div className="flex-1 overflow-y-auto p-8 relative">
          <Outlet />
          
          {/* Footer Subtraction UI */}
          <footer className="mt-12 py-6 border-t border-outline-variant text-[10px] text-slate-400 font-bold uppercase tracking-widest">
            <span>Contabil Along © 2026</span>
          </footer>
        </div>
      </main>
    </div>
  );
};

export default Layout;
