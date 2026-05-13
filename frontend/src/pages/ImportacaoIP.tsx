import React, { useState, useCallback, useRef } from 'react';
import axios from 'axios';
import { Upload, FileCheck, AlertCircle, Download, FileJson, Trash2, Loader2 } from 'lucide-react';
import { API_URL } from '../config';

interface FileMetrics {
  name: string;
  total_rows: number;
  linhas_exportadas: number;
  linhas_problema: number;
  soma_valor: number;
  soma_valor_ok: number;
}

const POLL_INTERVAL_MS = 3000;
const POLL_TIMEOUT_MS  = 600_000; // 10 min

const ImportacaoIP: React.FC = () => {
  const [files, setFiles]           = useState<File[]>([]);
  const [loading, setLoading]       = useState(false);
  const [loadingMsg, setLoadingMsg] = useState('PROCESSANDO...');
  const [results, setResults]       = useState<FileMetrics[]>([]);
  const [downloadUrl, setDownloadUrl]   = useState<string | null>(null);
  const [downloadName, setDownloadName] = useState<string>('tratados');
  const [error, setError]           = useState<string | null>(null);
  const [dragging, setDragging]     = useState(false);
  const pollTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) setFiles(Array.from(e.target.files));
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
    setLoadingMsg('ENVIANDO...');
    setError(null);
    if (downloadUrl) URL.revokeObjectURL(downloadUrl);
    setDownloadUrl(null);
    setResults([]);

    try {
      // 1. Enviar arquivos e obter job_id
      const formData = new FormData();
      files.forEach(f => formData.append('files', f));

      const { data: jobData } = await axios.post(`${API_URL}/api/ip/process`, formData);
      const jobId: string = jobData.job_id;

      setLoadingMsg('PROCESSANDO...');

      // 2. Fazer polling até o job terminar
      await new Promise<void>((resolve, reject) => {
        const deadline = Date.now() + POLL_TIMEOUT_MS;

        const poll = async () => {
          try {
            const { data } = await axios.get(`${API_URL}/api/ip/status/${jobId}`);
            if (data.status === 'done') return resolve();
            if (data.status === 'error') return reject(new Error(data.detail || 'Erro no processamento.'));
          } catch (e: any) {
            return reject(new Error(e.response?.data?.detail || 'Erro ao verificar status.'));
          }
          if (Date.now() > deadline) return reject(new Error('Tempo esgotado.'));
          pollTimer.current = setTimeout(poll, POLL_INTERVAL_MS);
        };

        poll();
      });

      setLoadingMsg('BAIXANDO...');

      // 3. Baixar resultado
      const response = await axios.get(`${API_URL}/api/ip/download/${jobId}`, {
        responseType: 'blob',
      });

      const metricsHeader = response.headers['x-all-metrics'];
      if (metricsHeader) setResults(JSON.parse(metricsHeader));

      const blob = new Blob([response.data], { type: response.headers['content-type'] });
      setDownloadUrl(URL.createObjectURL(blob));

      const disposition: string = response.headers['content-disposition'] ?? '';
      const match = disposition.match(/filename="?([^"]+)"?/);
      setDownloadName(match ? match[1] : files.length > 1 ? 'tratados.zip' : `tratado_${files[0].name}`);

    } catch (err: any) {
      if (pollTimer.current) clearTimeout(pollTimer.current);
      const msg = err.response?.data?.detail ?? err.message ?? 'Erro ao processar arquivos.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const totalExportadas = results.reduce((s, r) => s + r.linhas_exportadas, 0);
  const totalValor      = results.reduce((s, r) => s + r.soma_valor, 0);

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
        {/* Upload */}
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
                  <button onClick={() => { setFiles([]); setResults([]); setDownloadUrl(null); }} className="text-red-400 hover:text-red-600"><Trash2 size={14}/></button>
                </div>
                {files.map((f, i) => (
                  <div key={i} className="flex items-center gap-2 bg-surface-container-low p-2 rounded-lg text-xs font-bold text-primary">
                    <FileCheck size={14} className="text-green-500 flex-shrink-0" />
                    <span className="truncate flex-1">{f.name}</span>
                    <span className="text-slate-400 flex-shrink-0">{(f.size / 1024 / 1024).toFixed(1)} MB</span>
                  </div>
                ))}

                <button
                  onClick={processFiles}
                  disabled={loading}
                  className="w-full mt-4 bg-secondary hover:bg-primary-container text-white font-black py-4 rounded-xl transition-all shadow-lg shadow-secondary/20 flex items-center justify-center gap-2 disabled:opacity-50 disabled:grayscale"
                >
                  {loading
                    ? <><Loader2 size={16} className="animate-spin" />{loadingMsg}</>
                    : 'PROCESSAR ARQUIVOS'}
                </button>
              </div>
            )}
          </div>

          {error && (
            <div className="bg-red-50 border border-red-100 p-4 rounded-xl flex gap-3 text-red-600">
              <AlertCircle className="flex-shrink-0" size={18} />
              <p className="text-xs font-bold leading-relaxed">{error}</p>
            </div>
          )}
        </div>

        {/* Resultados */}
        <div className="lg:col-span-2">
          {results.length > 0 && downloadUrl ? (
            <div className="space-y-6">
              <div className="flex items-center justify-between bg-primary p-5 rounded-2xl text-white shadow-lg shadow-primary/20">
                <div>
                  <p className="text-xs font-black uppercase tracking-widest">
                    {results.length} arquivo{results.length > 1 ? 's' : ''} processado{results.length > 1 ? 's' : ''}
                  </p>
                  <p className="text-[10px] text-white/50 mt-0.5">
                    {totalExportadas.toLocaleString('pt-BR')} linhas exportadas
                  </p>
                </div>
                <a
                  href={downloadUrl}
                  download={downloadName}
                  className="flex items-center gap-2 px-5 py-3 bg-secondary text-white text-xs font-black uppercase tracking-widest rounded-xl hover:bg-white hover:text-secondary transition-all shadow-xl shadow-black/20 whitespace-nowrap"
                >
                  <Download size={16} /> Baixar {results.length > 1 ? '.zip' : '.csv'}
                </a>
              </div>

              {results.map((res, i) => (
                <div key={i} className="bg-surface rounded-2xl border border-outline-variant shadow-lg overflow-hidden animate-in zoom-in-95 duration-300">
                  <div className="bg-surface-container-low px-6 py-4 flex items-center gap-3 border-b border-outline-variant">
                    <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center border border-outline-variant shadow-sm">
                      <FileCheck size={18} className="text-green-500" />
                    </div>
                    <h4 className="font-black text-primary text-sm truncate">{res.name}</h4>
                  </div>
                  <div className="p-6 grid grid-cols-4 gap-4">
                    <div className="p-4 bg-background rounded-xl border border-outline-variant">
                      <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest leading-none">Linhas Totais</p>
                      <p className="text-lg font-black text-primary mt-1">{res.total_rows.toLocaleString('pt-BR')}</p>
                    </div>
                    <div className="p-4 bg-background rounded-xl border border-outline-variant">
                      <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest leading-none">Exportadas</p>
                      <p className="text-lg font-black text-secondary mt-1">{res.linhas_exportadas.toLocaleString('pt-BR')}</p>
                    </div>
                    <div className="p-4 bg-background rounded-xl border border-outline-variant">
                      <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest leading-none">Ignoradas</p>
                      <p className="text-lg font-black text-slate-500 mt-1">{(res.total_rows - res.linhas_exportadas).toLocaleString('pt-BR')}</p>
                    </div>
                    <div className="p-4 bg-background rounded-xl border border-outline-variant">
                      <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest leading-none">Valor Total</p>
                      <p className="text-lg font-black text-primary mt-1">R$ {res.soma_valor.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="h-[400px] bg-surface-container-low/30 border-2 border-dashed border-outline-variant rounded-2xl flex flex-col items-center justify-center text-slate-400 italic">
              {loading ? (
                <div className="flex flex-col items-center gap-4">
                  <Loader2 size={32} className="animate-spin text-secondary" />
                  <p className="text-xs font-bold uppercase tracking-widest opacity-70">{loadingMsg}</p>
                  <p className="text-[10px] opacity-40">Arquivos grandes podem levar alguns minutos</p>
                </div>
              ) : (
                <>
                  <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center mb-4 shadow-sm">
                    <FileJson size={24} className="opacity-20" />
                  </div>
                  <p className="text-xs font-bold uppercase tracking-widest opacity-50">Nenhum resultado processado ainda</p>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ImportacaoIP;
