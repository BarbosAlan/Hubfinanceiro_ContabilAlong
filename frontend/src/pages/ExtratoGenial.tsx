import React, { useState, useCallback } from 'react';
import axios from 'axios';
import { Upload, FileCheck, AlertCircle, Download, CreditCard, Table as TableIcon, Trash2, PieChart } from 'lucide-react';
import { API_URL } from '../config';

const ExtratoGenial: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const dropped = Array.from(e.dataTransfer.files).find(f => f.name.endsWith('.xlsx'));
    if (dropped) setFile(dropped);
  }, []);

  const processFile = async () => {
    if (!file) return;
    
    setLoading(true);
    setError(null);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API_URL}/api/genial/process`, formData);
      setResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao processar extrato.');
    } finally {
      setLoading(false);
    }
  };

  const downloadBase64 = (base64: string, filename: string) => {
    const link = document.createElement('a');
    link.href = `data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,${base64}`;
    link.download = filename;
    link.click();
  };

  return (
    <div className="max-w-6xl animate-in fade-in slide-in-from-bottom-4 duration-500">
      <header className="mb-8 p-8 bg-primary-container rounded-2xl text-white relative overflow-hidden">
        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-2">
            <span className="px-3 py-1 bg-secondary text-white font-black text-[10px] uppercase tracking-widest rounded-full">Processamento Premium</span>
            <span className="text-white/40 text-[10px] font-bold uppercase tracking-widest">Módulo 02</span>
          </div>
          <h1 className="text-2xl font-black tracking-tight">Extrato Genial / Banco</h1>
          <p className="text-white/60 text-sm mt-1 font-medium">Extração de dados de Excel com agrupamento inteligente de históricos complexos.</p>
        </div>
        <CreditCard size={120} className="absolute -right-4 -bottom-4 text-white/5 opacity-20 rotate-12" />
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Input Card */}
        <div className="lg:col-span-1">
          <div className="bg-surface p-6 rounded-2xl border border-outline-variant shadow-sm sticky top-24">
             <h3 className="text-xs font-black text-slate-400 uppercase tracking-widest mb-4 flex items-center gap-2">
              <Upload size={14} /> Seleção de Arquivo
            </h3>

            <label
              className={`group cursor-pointer block border-2 border-dashed rounded-xl p-8 text-center transition-all ${dragging ? 'border-secondary bg-blue-50 scale-[1.02]' : 'border-outline-variant hover:border-secondary hover:bg-surface-container-low'}`}
              onDragOver={e => { e.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              onDrop={handleDrop}
            >
              <input type="file" accept=".xlsx" onChange={handleFileChange} className="hidden" />
              <div className="w-12 h-12 bg-surface-container-low rounded-full flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform">
                <CreditCard className={`transition-colors ${dragging ? 'text-secondary' : 'text-slate-400 group-hover:text-secondary'}`} />
              </div>
              <p className="text-sm font-bold text-primary">{dragging ? 'Solte o arquivo aqui' : file ? 'Arquivo selecionado' : 'Clique ou arraste o arquivo'}</p>
              <p className="text-[10px] text-slate-400 font-bold uppercase mt-1 tracking-tighter">Somente planilhas .xlsx</p>
            </label>

            {file && (
               <div className="mt-6">
                <div className="flex items-center gap-3 bg-surface-container-low p-4 rounded-xl text-xs font-bold text-primary mb-4">
                  <FileCheck size={18} className="text-green-500 flex-shrink-0" />
                  <span className="truncate">{file.name}</span>
                </div>
                
                <button 
                  onClick={processFile}
                  disabled={loading}
                  className="w-full bg-secondary hover:bg-primary-container text-white font-black py-4 rounded-xl transition-all shadow-lg shadow-secondary/20 flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  {loading ? 'ANALISANDO...' : 'EXECUTAR TRATAMENTO'}
                </button>
                <button onClick={() => {setFile(null); setResult(null);}} className="w-full mt-2 text-[10px] font-black text-red-400 uppercase tracking-widest hover:text-red-600 transition-colors">
                  Limpar seleção
                </button>
              </div>
            )}

            {error && (
              <div className="mt-6 bg-red-50 border border-red-100 p-4 rounded-xl flex gap-3 text-red-600">
                <AlertCircle className="flex-shrink-0" />
                <p className="text-xs font-bold leading-relaxed">{error}</p>
              </div>
            )}
          </div>
        </div>

        {/* View Results */}
        <div className="lg:col-span-2">
           {result ? (
             <div className="space-y-6 animate-in zoom-in-95 duration-300">
                {/* Genial Stats Row */}
                <div className="grid grid-cols-3 gap-4">
                   <div className="bg-surface p-5 rounded-2xl border border-outline-variant shadow-sm border-l-4 border-l-secondary">
                      <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Linhas Originais</p>
                      <p className="text-2xl font-black text-primary mt-1">{result.stats.linhas_originais}</p>
                   </div>
                   <div className="bg-surface p-5 rounded-2xl border border-outline-variant shadow-sm border-l-4 border-l-green-500">
                      <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Saldo Final</p>
                      <p className={`text-2xl font-black mt-1 ${result.stats.saldo_final >= 0 ? 'text-green-600' : 'text-red-500'}`}>
                        R$ {result.stats.saldo_final?.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                      </p>
                   </div>
                   <div className="bg-surface p-5 rounded-2xl border border-outline-variant shadow-sm border-l-4 border-l-indigo-500">
                      <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Agrupadas</p>
                      <p className="text-2xl font-black text-primary mt-1">{result.stats.agrupados}</p>
                   </div>
                </div>

                <div className="bg-surface rounded-2xl border border-outline-variant shadow-lg overflow-hidden">
                   <div className="bg-primary p-6 flex justify-between items-center text-white">
                      <div>
                        <h4 className="font-black text-sm uppercase tracking-widest">TRATAMENTO CONCLUÍDO</h4>
                        <p className="text-[10px] text-white/50 font-medium mt-1">O arquivo foi limpo e os nomes foram normalizados.</p>
                      </div>
                      <button 
                        onClick={() => downloadBase64(result.output_base64, result.filename)}
                        className="flex items-center gap-2 px-6 py-3 bg-secondary text-white text-xs font-black uppercase tracking-widest rounded-xl hover:bg-white hover:text-secondary transition-all shadow-xl shadow-black/20"
                      >
                        <Download size={16} /> Baixar Planilha (.xlsx)
                      </button>
                   </div>

                   <div className="p-6">
                      <div className="flex items-center gap-2 mb-4 text-[10px] font-black text-slate-400 uppercase tracking-widest">
                         <TableIcon size={14} /> Dados Processados (Preview)
                      </div>
                      <div className="border border-outline-variant rounded-xl overflow-hidden shadow-inner">
                        <div className="overflow-x-auto max-h-[400px]">
                          <table className="w-full text-[11px] text-left border-collapse">
                            <thead className="bg-background sticky top-0 z-10 border-b border-outline-variant">
                              <tr>
                                <th className="px-4 py-4 font-black text-primary">DATA</th>
                                <th className="px-4 py-4 font-black text-primary">HISTÓRICO</th>
                                <th className="px-4 py-4 font-black text-primary text-right">ENTRADAS</th>
                                <th className="px-4 py-4 font-black text-primary text-right">SAÍDAS</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-outline-variant bg-white">
                              {result.preview.map((row: any, idx: number) => (
                                <tr key={idx} className="hover:bg-blue-50/50 transition-colors">
                                  <td className="px-4 py-4 font-bold text-slate-500 whitespace-nowrap">{row.Data}</td>
                                  <td className="px-4 py-4">
                                     <p className="font-black text-primary text-[10px]">{row['HISTORICO']}</p>
                                     <p className="text-[9px] text-slate-400 font-medium truncate max-w-[250px] uppercase">Lançamento: {row['HISTORICO DE LANÇAMENTO']}</p>
                                  </td>
                                  <td className="px-4 py-4 font-black text-green-600 text-right">
                                    {row.Valor > 0 ? `+ R$ ${Math.abs(row.Valor).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}` : '-'}
                                  </td>
                                  <td className="px-4 py-4 font-black text-red-500 text-right">
                                    {row.Valor < 0 ? `- R$ ${Math.abs(row.Valor).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}` : '-'}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                   </div>
                </div>
             </div>
           ) : (
             <div className="h-[550px] bg-white border border-outline-variant rounded-2xl border-dashed flex flex-col items-center justify-center text-slate-400">
               <div className="relative mb-6">
                  <div className="absolute inset-0 bg-secondary/10 blur-3xl rounded-full"></div>
                  <PieChart size={64} className="relative text-slate-200 opacity-50" />
               </div>
               <p className="text-xs font-black uppercase tracking-[0.2em] opacity-40">Aguardando arquivo para análise</p>
             </div>
           )}
        </div>
      </div>
    </div>
  );
};

export default ExtratoGenial;
