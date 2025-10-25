import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Register from './components/Register';
import Login from './components/Login';
import CreateAccount from './components/createaccount';
import Dashboard from './components/Dashboard';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/register" element={<Register />} />
          <Route path="/login" element={<Login />} />
          <Route path="/create-account" element={<CreateAccount />} />
          <Route path="/dashboard/:userId" element={<Dashboard />} />
          <Route path="/" element={<h1>SmartBank Demo</h1>} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;