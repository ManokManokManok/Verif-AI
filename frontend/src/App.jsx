import { Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Landing from './pages/Landing.jsx';
import Login from './pages/Login.jsx';
import Signup from './pages/Signup.jsx';
import Detection from './pages/Detection.jsx';
import AIChatbot from './pages/AIChatbot.jsx';
import BlockchainPage from './pages/Blockchain.jsx';

function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/detection" element={<Detection />} />
        <Route path="/chatbot" element={<AIChatbot />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/blockchain" element={<BlockchainPage />} />
      </Routes>
    </AuthProvider>
  );
}

export default App;

