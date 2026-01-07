import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Navbar.css';

export const Navbar = () => {
  const { isAuthenticated, user, logout } = useAuth();

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/" className="navbar-brand">
          Product Generator
        </Link>
        <div className="navbar-links">
          <Link to="/" className="navbar-link">
            Generate
          </Link>
          {isAuthenticated && (
            <Link to="/history" className="navbar-link">
              History
            </Link>
          )}
          {isAuthenticated ? (
            <>
              <span className="navbar-user">Welcome, {user?.username}!</span>
              <button onClick={logout} className="navbar-button">
                Logout
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="navbar-link">
                Login
              </Link>
              <Link to="/register" className="navbar-button">
                Register
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
};



