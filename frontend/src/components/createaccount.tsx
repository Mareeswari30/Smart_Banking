import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const CreateAccount: React.FC = () => {
  const [accType, setAccType] = useState<string>('savings');
  const [userId, setUserId] = useState<string>('');
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const token = localStorage.getItem('token');
    if (!token) return alert('Please login first');

    try {
      await axios.post(
        'http://localhost:8000/account',
        { user_id: userId, acc_type: accType },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      alert('Account created!');
      navigate(`/dashboard/${userId}`);
    } catch (err: any) {
      alert('Error: ' + (err.response?.data?.detail || 'Account creation failed'));
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Create Account</h2>
      <input
        type="text"
        placeholder="Your User ID"
        value={userId}
        onChange={(e) => setUserId(e.target.value)}
        required
      />
      <select value={accType} onChange={(e) => setAccType(e.target.value)}>
        <option value="savings">Savings</option>
        <option value="checking">Checking</option>
      </select>
      <button type="submit">Create Account</button>
    </form>
  );
};

export default CreateAccount;