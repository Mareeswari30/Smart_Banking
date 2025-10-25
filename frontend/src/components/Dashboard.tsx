import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useParams, useNavigate } from 'react-router-dom';

interface Account {
  user_id: string;
  account_number: string;
  balance: number;
  acc_type: string;
}

interface Transaction {
  from_account: string;
  to_account: string;
  amount: number;
  timestamp: string;
}

interface DashboardData {
  kyc_status?: string;
  accounts: Account[];
  transactions: Transaction[];
}

const Dashboard: React.FC = () => {
  const { userId } = useParams<{ userId: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<DashboardData>({
    accounts: [],
    transactions: [],
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const token = localStorage.getItem('token');

  useEffect(() => {
    if (!token || !userId) {
      setError('Please login');
      navigate('/login');
      setLoading(false);
      return;
    }
    const fetchData = async () => {
      try {
        setLoading(true);
        const res = await axios.get(`http://localhost:8000/dashboard/${userId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setData(res.data);
        setError(null);
      } catch (error) {
        if (axios.isAxiosError(error)) {
    setError(error.response?.data?.detail || 'Failed to load dashboard');
      }
      else if (error instanceof Error) {
    setError(error.message);
  } else {
    setError('Failed to load dashboard');
  } 
}
      finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [userId, token, navigate]);

  if (loading) return <p>Loading dashboard...</p>;

  return (
    <div>
      <h2>Dashboard for User {userId}</h2>
      {error && <div className="error">{error}</div>}
      {data.kyc_status && (
        <>
          <h3>KYC Status: {data.kyc_status.toUpperCase()}</h3>
          {data.kyc_status !== 'approved' && (
            <p className="kyc-warning">Please complete KYC verification to create accounts.</p>
          )}
        </>
      )}
      
      <h3>Accounts</h3>
      <ul>
        {data.accounts.length ? (
          data.accounts.map((acc, idx) => (
            <li key={idx}>
              {acc.account_number} - {acc.acc_type} - Balance: ${acc.balance}
            </li>
          ))
        ) : (
          <p>No accounts found.</p>
        )}
      </ul>
      <h3>Transactions</h3>
      <ul>
        {data.transactions.length ? (
          data.transactions.map((tx, idx) => (
            <li key={idx}>
              From: {tx.from_account} To: {tx.to_account} Amount: ${tx.amount} at{' '}
              {new Date(tx.timestamp).toLocaleString()}
            </li>
          ))
        ) : (
          <p>No transactions found.</p>
        )}
      </ul>
    </div>
  );
};

export default Dashboard;
