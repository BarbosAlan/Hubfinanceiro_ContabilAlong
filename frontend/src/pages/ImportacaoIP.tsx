import React, { useState, useCallback } from 'react';
import axios from 'axios';
import { Upload, FileCheck, AlertCircle, Download, FileJson, Table as TableIcon, Trash2 } from 'lucide-react';
import { API_URL } from '../config';

const ImportacaoIP: React.FC = () => {
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any[]>([]);
  const [allZipBase64, setAllZipBase64] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files));
    }
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const dropped = Array.from(e.dataTransfer.files).filter(f => f.name.endsWith('.csv'));
    if (dropped.length) setFiles(dropped);
  }, []);

  const processFiles = async () => {
    if (files.length === 0) return;
    
    setLoading(true);
    setError(null);
    const formData = new FormData();
    files.forEach(f => formData.append('files', f));

    try {
      const response = await axios.post(`${API_URL}/api/ip/process`, formData);
      setResults(response.data.results);
      setAllZipBase64(response.data.all_zip_base64 ?? null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao processar arquivos.');
    } finally {
      setLoading(false);
    }
  };

  const downloadBase64 = (base64: string, filename: string) => {
    const link = document.createElement('a');
    link.href = `data:application/octet-stream;base64,${base64}`;
    link.download = filename;
    link.click();
  };

  return (
    <div className="max-w-6xl animate-in fade-in slide-in-from-bottom-4 duration-500">
      <header className="mb-8 p-8 bg-primary rounded-2xl text-white relative overflow-hidden">
        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-2">
            <span className="px-3 py-1 bg-secondary-container text-primary font-black text-[10px] uppercase tracking-widest rounded-full">Automático</span>
            <span className="text-white/40 text-[10px] font-bold uppercase tracking-widest">Módulo 01</span>
          </div>
          <h1 className="text-2xl font-black tracking-tight">Importação Transações IP</h1>
          <p className="text-white/60 text-sm mt-1 font-medium">Tratamento de extratos CSV com geração de registros contábeis consolidados.</p>
        </div>
        <FileJson size={120} className="absolute -right-4 -bottom-4 text-white/5 opacity-20 rotate-12" />
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Upload Section */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-surface p-6 rounded-2xl border border-outline-variant shadow-sm">
            <h3 className="text-xs font-black text-slate-400 uppercase tracking-widest mb-4 flex items-center gap-2">
              <Upload size={14} /> Upload de Arquivos
            </h3>
            
            <label
              className={`group cursor-pointer block border-2 border-dashed rounded-xl p-8 text-center transition-all ${dragging ? 'border-secondary bg-blue-50 scale-[1.02]' : 'border-outline-variant hover:border-secondary hover:bg-surface-container-low'}`}
              onDragOver={e => { e.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              onDrop={handleDrop}
            >
              <input type="file" multiple accept=".csv" onChange={handleFileChange} className="hidden" />
              <div className="w-12 h-12 bg-surface-container-low rounded-full flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform">
                <Upload className={`transition-colors ${dragging ? 'text-secondary' : 'text-slate-400 group-hover:text-secondary'}`} />
              </div>
              <p className="text-sm font-bold text-primary">{dragging ? 'Solte os arquivos aqui' : 'Clique ou arraste os arquivos'}</p>
              <p className="text-[10px] text-slate-400 font-bold uppercase mt-1 tracking-tighter">Somente arquivos .csv</p>
            </label>

            {files.length > 0 && (
              <div className="mt-6 space-y-2">
                <div className="flex justify-between items-center mb-2">
                   <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Selecionados ({files.length})</p>
                   <button onClick={() => { setFiles([]); setResults([]); setAllZipBase64(null); }} className="text-red-400 hover:text-red-600"><Trash2 size={14}/></button>
                </div>
                {files.map((f, i) => (
                  <div key={i} className="flex items-center gap-2 bg-surface-container-low p-2 rounded-lg text-xs font-bold text-primary truncate">
                    <FileCheck size={14} className="text-green-500 flex-shrink-0" />
                    <span className="truncate">{f.name}</span>
                  </div>
                ))}
                
                <button 
                  onClick={processFiles}
                  disabled={loading || files.length === 0}
                  className="w-full mt-4 bg-secondary hover:bg-primary-container text-white font-black py-4 rounded-xl transition-all shadow-lg shadow-secondary/20 flex items-center justify-center gap-2 disabled:opacity-50 disabled:grayscale"
                >
                  {loading ? 'PROCESSANDO...' : 'PROCESSAR ARQUIVOS'}
                </button>
              </div>
            )}
          </div>

          {error && (
            <div className="bg-red-50 border border-red-100 p-4 rounded-xl flex gap-3 text-red-600">
              <AlertCircle className="flex-shrink-0" />
              <p className="text-xs font-bold leading-relaxed">{error}</p>
            </div>
          )}
        </div>

        {/* Results Section */}
        <div className="lg:col-span-2">
          {results.length > 0 ? (
            <div className="space-y-6">
              {allZipBase64 && (
                <div className="flex items-center justify-between bg-primary p-5 rounded-2xl text-white shadow-lg shadow-primary/20">
                  <div>
                    <p className="text-xs font-black uppercase tracking-widest">{results.length} arquivos processados</p>
                    <p className="text-[10px] text-white/50 mt-0.5">Baixe todos de uma vez em um único arquivo .zip</p>
                  </div>
                  <button
                    onClick={() => downloadBase64(allZipBase64, 'tratados.zip')}
                    className="flex items-center gap-2 px-5 py-3 bg-secondary text-white text-xs font-black uppercase tracking-widest rounded-xl hover:bg-white hover:text-secondary transition-all shadow-xl shadow-black/20 whitespace-nowrap"
                  >
                    <Download size={16} /> Baixar Todos (.zip)
                  </button>
                </div>
              )}
              {results.map((res, i) => (
                <div key={i} className="bg-surface rounded-2xl border border-outline-variant shadow-lg overflow-hidden animate-in zoom-in-95 duration-300">
                  <div className="bg-surface-container-low px-6 py-4 flex justify-between items-center border-b border-outline-variant">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center border border-outline-variant shadow-sm">
                        <FileCheck size={18} className="text-green-500" />
                      </div>
                      <h4 className="font-black text-primary text-sm truncate max-w-[200px]">{res.name}</h4>
                    </div>
                    <div className="flex gap-2">
                       {res.errors_base64 && (
                         <button 
                          onClick={() => downloadBase64(res.errors_base64, `erros_${res.name}`)}
                          className="flex items-center gap-2 px-3 py-1.5 bg-red-100 text-red-600 text-[10px] font-black uppercase tracking-widest rounded-lg hover:bg-red-200 transition-colors"
                        >
                          Log de Erros
                        </button>
                       )}
                       <button 
                        onClick={() => downloadBase64(res.output_base64, `tratado_${res.name}`)}
                        className="flex items-center gap-2 px-4 py-1.5 bg-secondary text-white text-[10px] font-black uppercase tracking-widest rounded-lg hover:bg-primary-container transition-all shadow-md shadow-secondary/10"
                      >
                        <Download size={14} /> Baixar CSV
                      </button>
                    </div>
                  </div>

                  <div className="p-6">
                    {/* Mini Metrics */}
                    <div className="grid grid-cols-4 gap-4 mb-6">
                      <div className="p-4 bg-background rounded-xl border border-outline-variant">
                        <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest leading-none">Linhas Totais</p>
                        <p className="text-lg font-black text-primary mt-1">{res.metrics.total_rows}</p>
                      </div>
                      <div className="p-4 bg-background rounded-xl border border-outline-variant">
                        <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest leading-none">Exportadas</p>
                        <p className="text-lg font-black text-secondary mt-1">{res.metrics.linhas_exportadas}</p>
                      </div>
                      <div className="p-4 bg-background rounded-xl border border-outline-variant col-span-2">
                        <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest leading-none">Valor Consolidado</p>
                        <p className="text-lg font-black text-primary mt-1">R$ {res.metrics.soma_valor.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</p>
                      </div>
                    </div>

                    {/* Preview Table */}
                    <div className="border border-outline-variant rounded-xl overflow-hidden">
                       <div className="bg-surface-container-low px-4 py-2 border-b border-outline-variant flex items-center gap-2 text-[9px] font-black text-slate-400 uppercase tracking-widest">
                         <TableIcon size={12} /> Pré-visualização (Primeiras 5 linhas)
                       </div>
                       <div className="overflow-x-auto">
                          <table className="w-full text-[11px] text-left">
                            <thead className="bg-white border-b border-outline-variant">
                              <tr>
                                <th className="px-4 py-3 font-black text-primary">DATA</th>
                                <th className="px-4 py-3 font-black text-primary text-right">VALOR</th>
                                <th className="px-4 py-3 font-black text-primary">DESCRIÇÃO</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-outline-variant bg-white">
                              {res.preview.slice(0, 5).map((row: any, idx: number) => (
                                <tr key={idx} className="hover:bg-background transition-colors">
                                  <td className="px-4 py-3 font-bold text-slate-500">{row.Data}</td>
                                  <td className="px-4 py-3 font-black text-primary text-right whitespace-nowrap">R$ {row.Valor}</td>
                                  <td className="px-4 py-3 text-slate-400 font-medium truncate max-w-[300px]">{row["Resumo da Transação"]}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                       </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="h-[400px] bg-surface-container-low/30 border-2 border-dashed border-outline-variant rounded-2xl flex flex-col items-center justify-center text-slate-400 italic">
               <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center mb-4 shadow-sm">
                  <FileJson size={24} className="opacity-20" />
               </div>
               <p className="text-xs font-bold uppercase tracking-widest opacity-50">Nenhum resultado processado ainda</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ImportacaoIP;
