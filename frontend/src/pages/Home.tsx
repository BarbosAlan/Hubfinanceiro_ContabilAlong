import React from 'react';
import { Link } from 'react-router-dom';
import { FileText, CreditCard, ArrowUpRight } from 'lucide-react';

const Home: React.FC = () => {
  const modules = [
    {
      title: 'Importação Transações IP',
      desc: 'Tratamento de arquivos CSV de transações para o formato contábil padrão.',
      path: '/ip',
      icon: FileText,
      color: 'bg-blue-50 text-secondary',
    },
    {
      title: 'Extrato Genial/Banco',
      desc: 'Processamento inteligente de extratos bancários com agrupamento dinâmico.',
      path: '/genial',
      icon: CreditCard,
      color: 'bg-indigo-50 text-primary-container',
    }
  ];

  return (
    <div className="max-w-6xl animate-in fade-in slide-in-from-bottom-4 duration-500">
      <header className="mb-10">
        <h1 className="text-3xl font-black text-primary tracking-tight">Bem-vindo ao Hub Financeiro</h1>
        <p className="text-slate-500 mt-2 font-medium">Selecione um módulo abaixo para começar a processar seus dados.</p>
      </header>

      <div className="section-header flex items-center gap-4 mb-6">
        <h2 className="text-xs font-black text-slate-400 uppercase tracking-[0.2em] whitespace-nowrap">Módulos Disponíveis</h2>
        <div className="h-[1px] w-full bg-outline-variant"></div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {modules.map((module, i) => (
          <Link 
            key={i} 
            to={module.path}
            className="group relative bg-surface p-8 rounded-2xl border border-outline-variant shadow-sm hover:shadow-xl transition-all duration-300 overflow-hidden"
          >
            {/* Hover Decorator */}
            <div className="absolute top-0 left-0 w-full h-[4px] bg-gradient-to-r from-secondary to-secondary-container opacity-0 group-hover:opacity-100 transition-opacity"></div>
            
            <div className={`w-14 h-14 ${module.color} flex items-center justify-center rounded-xl mb-6 shadow-inner transition-transform group-hover:scale-110 duration-300`}>
              <module.icon size={28} />
            </div>

            <div className="flex items-center gap-2 mb-2">
              <h3 className="text-xl font-black text-primary tracking-tight">{module.title}</h3>
              <ArrowUpRight size={18} className="text-slate-300 group-hover:text-secondary group-hover:translate-x-1 group-hover:-translate-y-1 transition-all" />
            </div>
            
            <p className="text-sm text-slate-500 leading-relaxed font-medium mb-6">
              {module.desc}
            </p>

            <div className="flex items-center gap-2 text-[11px] font-black text-secondary uppercase tracking-[0.15em]">
              Acessar Módulo
              <div className="h-1 w-8 bg-surface-container-low rounded-full overflow-hidden">
                <div className="h-full bg-secondary w-0 group-hover:w-full transition-all duration-500"></div>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
};

export default Home;
