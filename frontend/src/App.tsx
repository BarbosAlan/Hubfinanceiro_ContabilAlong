import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Home from './pages/Home';
import ImportacaoIP from './pages/ImportacaoIP';
import ExtratoGenial from './pages/ExtratoGenial';
import ExcelToCsv from './pages/ExcelToCsv';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="ip" element={<ImportacaoIP />} />
          <Route path="genial" element={<ExtratoGenial />} />
          <Route path="excel-to-csv" element={<ExcelToCsv />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
