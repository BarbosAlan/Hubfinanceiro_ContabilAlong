import React, { useState, useCallback } from 'react';
import axios from 'axios';
import { Upload, FileCheck, AlertCircle, Download, FileSpreadsheet, CheckCircle } from 'lucide-react';
import { API_URL } from '../config';

const ExcelToCsv: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setResult(null);
      setError(null);
    }
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const dropped = Array.from(e.dataTransfer.files).find(f => f.name.endsWith('.xlsx'));
    if (dropped) {
      setFile(dropped);
      setResult(null);
      setError(null);
    }
  }, []);

  const processFile = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API_URL}/api/excel-to-csv/process`, formData);
      setResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao converter o arquivo.');
    } finally {
      setLoading(false);
    }
  };

  const downloadCsv = (base64: string, filename: string) => {
    const blob = new Blob([Uint8Array.from(atob(base64), c => c.charCodeAt(0))], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="max-w-3xl animate-in fade-in slide-in-from-bottom-4 duration-500">
      <header className="mb-8 p-8 bg-primary-container rounded-2xl text-white relative overflow-hidden">
        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-2">
            <span className="px-3 py-1 bg-secondary text-white font-black text-[10px] uppercase tracking-widest rounded-full">Conversão</span>
            <span className="text-white/40 text-[10px] font-bold uppercase tracking-widest">Módulo 03</span>
          </div>
          <h1 className="text-2xl font-black tracking-tight">Excel para CSV</h1>
          <p className="text-white/60 text-sm mt-1 font-medium">Converte qualquer planilha .xlsx em arquivo .csv com separador vírgula.</p>
        </div>
        <FileSpreadsheet size={120} className="absolute -right-4 -bottom-4 text-white/5 opacity-20 rotate-12" />
      </header>

      <div className="bg-surface p-6 rounded-2xl border border-outline-variant shadow-sm">
        <h3 className="text-xs font-black text-slate-400 uppercase tracking-widest mb-4 flex items-center gap-2">
          <Upload size={14} /> Seleção de Arquivo
        </h3>

        <label
          className={`group cursor-pointer block border-2 border-dashed rounded-xl p-10 text-center transition-all ${dragging ? 'border-secondary bg-blue-50 scale-[1.02]' : 'border-outline-variant hover:border-secondary hover:bg-surface-container-low'}`}
          onDragOver={e => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
        >
          <input type="file" accept=".xlsx" onChange={handleFileChange} className="hidden" />
          <div className="w-14 h-14 bg-surface-container-low rounded-full flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform">
            <FileSpreadsheet className={`transition-colors ${dragging ? 'text-secondary' : 'text-slate-400 group-hover:text-secondary'}`} />
          </div>
          <p className="text-sm font-bold text-primary">{dragging ? 'Solte o arquivo aqui' : file ? 'Arquivo selecionado' : 'Clique ou arraste o arquivo'}</p>
          <p className="text-[10px] text-slate-400 font-bold uppercase mt-1 tracking-tighter">Somente planilhas .xlsx · Até 100 MB</p>
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
              {loading ? 'CONVERTENDO...' : 'CONVERTER PARA CSV'}
            </button>
            <button onClick={() => { setFile(null); setResult(null); setError(null); }} className="w-full mt-2 text-[10px] font-black text-red-400 uppercase tracking-widest hover:text-red-600 transition-colors">
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

        {result && (
          <div className="mt-6 animate-in zoom-in-95 duration-300">
            <div className="bg-primary rounded-2xl p-6 flex items-center justify-between text-white">
              <div className="flex items-center gap-4">
                <CheckCircle size={32} className="text-green-400 flex-shrink-0" />
                <div>
                  <p className="font-black text-sm uppercase tracking-widest">Conversão concluída</p>
                  <p className="text-white/50 text-[11px] mt-1">{result.row_count} linhas · {result.col_count} colunas</p>
                </div>
              </div>
              <button
                onClick={() => downloadCsv(result.output_base64, result.filename)}
                className="flex items-center gap-2 px-6 py-3 bg-secondary text-white text-xs font-black uppercase tracking-widest rounded-xl hover:bg-white hover:text-secondary transition-all shadow-xl shadow-black/20 flex-shrink-0"
              >
                <Download size={16} /> Baixar CSV
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ExcelToCsv;
