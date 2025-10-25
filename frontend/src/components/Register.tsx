import React, { useState } from 'react';

import axios, { AxiosError } from 'axios';

const Register: React.FC = () => {
  const [name, setName] = useState<string>('');
  const [email, setEmail] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [documents, setDocuments] = useState<File[]>([]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append('name', name);
    formData.append('email', email);
    formData.append('password', password);
    documents.forEach((doc) => formData.append('documents', doc));

    try {
      const res = await axios.post('http://localhost:8000/register', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      alert(`Registered! User ID: ${res.data.user_id}`);
    } catch (err: AxiosError) {
      alert('Error: ' + ((err.response?.data as any)?.detail || 'Registration failed')); // Use 'as any' temporarily for response.data
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Register</h2>
      <input
        type="text"
        placeholder="Name"
        value={name}
        onChange={(e) => setName(e.target.value)}
        required
      />
      <input
        type="email"
        placeholder="Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
      />
      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
      />
      <input
        type="file"
        multiple
        onChange={(e) => setDocuments(e.target.files ? Array.from(e.target.files) : [])}
      />
      <button type="submit">Register</button>
    </form>
  );
};

export default Register;