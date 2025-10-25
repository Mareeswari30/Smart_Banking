# SmartBank – Modular Banking System

Built with **FastAPI**, it demonstrates modern API design, JWT authentication, and file handling.

---

## Features

- **User Registration:** Signup with document upload & password hashing.
- **Account Creation:** Create bank accounts with initial deposit of 500 units.

- **Dashboard:** View all accounts and transaction history.

---

## Tech Stack

- **Frontend:** React.js  
- **Backend:** FastAPI (Python)  
- **Database:** SQlite3
- **Security:** JWT authentication, bcrypt password hashing  
- **Testing:** Pytest  

---

## Database Design

### Users
- `name`, `email`, `password`, `mobile_number`, `documents`

### Accounts
- `user_id`, `account_number`, `balance`, `acc_type`



## API Endpoints


| POST | `/register` | User signup with document upload |
| POST | `/login` | User login and JWT token |
| POST | `/account` | Create a new bank account |
| GET  | `/dashboard/{user_id}` | Get user accounts and transactions |

---

## Security & Validation

- Passwords hashed with **bcrypt**  
- File uploads allowed: `.jpg`, `.jpeg`, `.png` (max 5MB)  
- Uploaded files saved with **unique filenames**  
- JWT-protected endpoints for authenticated access  

---

## Testing

- Pytest validates:
  - User registration & password verification  
  - Account creation & initial balance  
  - Money transfer validation  
  - Dashboard & transaction retrieval  
- All core functionalities passing with proper logging.

---

## Getting Started

1. Clone the repo:  
   ```bash
   git clone <repo_url>
   cd smartbank-backend
