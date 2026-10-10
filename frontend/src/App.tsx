import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './layouts/Layout';
import Dashboard from './pages/Dashboard';
import Scanner from './pages/Scanner';
import ScannerResult from './pages/ScannerResult';
import AddPlant from './pages/AddPlant';
import Plants from './pages/Plants';
import Assistant from './pages/Assistant';
import Health from './pages/Health';
import Watering from './pages/Watering';
import Insights from './pages/Insights';
import Settings from './pages/Settings';
import Help from './pages/Help';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="plants" element={<Plants />} />
          <Route path="plants/add" element={<AddPlant />} />
          <Route path="scanner" element={<Scanner />} />
          <Route path="scanner/result/:id" element={<ScannerResult />} />
          <Route path="assistant" element={<Assistant />} />
          <Route path="health" element={<Health />} />
          <Route path="watering" element={<Watering />} />
          <Route path="insights" element={<Insights />} />
          <Route path="settings" element={<Settings />} />
          <Route path="help" element={<Help />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
