import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Activity, Home, Calendar, MessageCircle, Settings, LogOut, BarChart3 } from 'lucide-react';

export const Navbar = () => {
  const { user, logout, isAdmin } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="bg-white shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Logo */}
          <div className="flex items-center">
            <Link to="/dashboard" className="flex items-center space-x-2">
              <div className="bg-blue-600 p-2 rounded-lg">
                <Activity className="w-6 h-6 text-white" />
              </div>
              <span className="text-xl font-bold text-gray-900">MindCare AI</span>
            </Link>
          </div>

          {/* Nav Links */}
          <div className="flex items-center space-x-4">
            <Link
              to="/dashboard"
              className={`flex items-center space-x-1 px-3 py-2 rounded-lg transition ${
                isActive('/dashboard')
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <Home className="w-5 h-5" />
              <span className="hidden sm:inline">Dashboard</span>
            </Link>

            <Link
              to="/chat"
              className={`flex items-center space-x-1 px-3 py-2 rounded-lg transition ${
                isActive('/chat')
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <MessageCircle className="w-5 h-5" />
              <span className="hidden sm:inline">Chat</span>
            </Link>

            <Link
              to="/book-counselor"
              className={`flex items-center space-x-1 px-3 py-2 rounded-lg transition ${
                isActive('/book-counselor')
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <Calendar className="w-5 h-5" />
              <span className="hidden sm:inline">Book Counselor</span>
            </Link>

            {isAdmin && (
              <Link
                to="/admin"
                className={`flex items-center space-x-1 px-3 py-2 rounded-lg transition ${
                  isActive('/admin')
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <BarChart3 className="w-5 h-5" />
                <span className="hidden sm:inline">Admin</span>
              </Link>
            )}

            {/* User Menu */}
            <div className="flex items-center space-x-3 ml-4 pl-4 border-l border-gray-300">
              <div className="text-right hidden sm:block">
                <p className="text-sm font-medium text-gray-900">{user?.full_name}</p>
                <p className="text-xs text-gray-500">{user?.email}</p>
              </div>
              <button
                onClick={handleLogout}
                className="flex items-center space-x-1 px-3 py-2 text-red-600 hover:bg-red-50 rounded-lg transition"
              >
                <LogOut className="w-5 h-5" />
                <span className="hidden sm:inline">Logout</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};