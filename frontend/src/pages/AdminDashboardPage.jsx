import { useState, useEffect } from 'react';
import { Navbar } from '../components/Navbar';
import { adminAPI } from '../utils/api';
import { Users, MessageSquare, Calendar, TrendingUp, User, Mail, Shield } from 'lucide-react';

export const AdminDashboardPage = () => {
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [counselors, setCounselors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    loadAdminData();
  }, []);

  const loadAdminData = async () => {
    try {
      const [statsRes, usersRes, counselorsRes] = await Promise.all([
        adminAPI.getStats(),
        adminAPI.getUsers(),
        adminAPI.getCounselors()
      ]);

      setStats(statsRes.data);
      setUsers(usersRes.data);
      setCounselors(counselorsRes.data);
    } catch (error) {
      console.error('Failed to load admin data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <>
        <Navbar />
        <div className="min-h-screen flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between mb-8">
            <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
            <div className="flex items-center space-x-2 bg-blue-100 px-4 py-2 rounded-lg">
              <Shield className="w-5 h-5 text-blue-600" />
              <span className="text-sm font-medium text-blue-700">Administrator</span>
            </div>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-xl shadow-md p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="bg-blue-100 p-3 rounded-lg">
                  <Users className="w-6 h-6 text-blue-600" />
                </div>
                <TrendingUp className="w-5 h-5 text-green-500" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900">{stats?.total_users || 0}</h3>
              <p className="text-sm text-gray-500">Total Users</p>
            </div>

            <div className="bg-white rounded-xl shadow-md p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="bg-green-100 p-3 rounded-lg">
                  <MessageSquare className="w-6 h-6 text-green-600" />
                </div>
                <TrendingUp className="w-5 h-5 text-green-500" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900">{stats?.total_sessions || 0}</h3>
              <p className="text-sm text-gray-500">Total Sessions</p>
            </div>

            <div className="bg-white rounded-xl shadow-md p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="bg-purple-100 p-3 rounded-lg">
                  <Calendar className="w-6 h-6 text-purple-600" />
                </div>
                <TrendingUp className="w-5 h-5 text-green-500" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900">{stats?.total_appointments || 0}</h3>
              <p className="text-sm text-gray-500">Appointments</p>
            </div>

            <div className="bg-white rounded-xl shadow-md p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="bg-yellow-100 p-3 rounded-lg">
                  <MessageSquare className="w-6 h-6 text-yellow-600" />
                </div>
                <TrendingUp className="w-5 h-5 text-green-500" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900">{stats?.total_conversations || 0}</h3>
              <p className="text-sm text-gray-500">Conversations</p>
            </div>
          </div>

          {/* Tabs */}
          <div className="bg-white rounded-xl shadow-md mb-6">
            <div className="border-b border-gray-200">
              <div className="flex space-x-8 px-6">
                <button
                  onClick={() => setActiveTab('overview')}
                  className={`py-4 border-b-2 font-medium text-sm transition ${
                    activeTab === 'overview'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Overview
                </button>
                <button
                  onClick={() => setActiveTab('users')}
                  className={`py-4 border-b-2 font-medium text-sm transition ${
                    activeTab === 'users'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Users ({users.length})
                </button>
                <button
                  onClick={() => setActiveTab('counselors')}
                  className={`py-4 border-b-2 font-medium text-sm transition ${
                    activeTab === 'counselors'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Counselors ({counselors.length})
                </button>
              </div>
            </div>

            {/* Tab Content */}
            <div className="p-6">
              {activeTab === 'overview' && (
                <div>
                  <h2 className="text-xl font-bold text-gray-900 mb-4">System Overview</h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="border border-gray-200 rounded-lg p-4">
                      <h3 className="font-semibold text-gray-900 mb-2">Recent Activity</h3>
                      <p className="text-sm text-gray-600">
                        Last 30 days: {stats?.total_sessions || 0} sessions completed
                      </p>
                    </div>
                    <div className="border border-gray-200 rounded-lg p-4">
                      <h3 className="font-semibold text-gray-900 mb-2">User Engagement</h3>
                      <p className="text-sm text-gray-600">
                        Average: {stats?.total_conversations 
                          ? (stats.total_conversations / stats.total_users).toFixed(1) 
                          : 0} messages per user
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'users' && (
                <div>
                  <h2 className="text-xl font-bold text-gray-900 mb-4">User Management</h2>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            User
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Email
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Status
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Role
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Joined
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {users.map((user) => (
                          <tr key={user._id} className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center">
                                <div className="bg-blue-100 w-10 h-10 rounded-full flex items-center justify-center">
                                  <User className="w-5 h-5 text-blue-600" />
                                </div>
                                <div className="ml-4">
                                  <div className="text-sm font-medium text-gray-900">
                                    {user.full_name}
                                  </div>
                                  <div className="text-sm text-gray-500">@{user.username}</div>
                                </div>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center text-sm text-gray-900">
                                <Mail className="w-4 h-4 mr-2 text-gray-400" />
                                {user.email}
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                                user.is_active
                                  ? 'bg-green-100 text-green-800'
                                  : 'bg-red-100 text-red-800'
                              }`}>
                                {user.is_active ? 'Active' : 'Inactive'}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {user.is_admin ? (
                                <span className="flex items-center text-purple-600">
                                  <Shield className="w-4 h-4 mr-1" />
                                  Admin
                                </span>
                              ) : (
                                'User'
                              )}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {new Date(user.created_at).toLocaleDateString()}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {activeTab === 'counselors' && (
                <div>
                  <h2 className="text-xl font-bold text-gray-900 mb-4">Counselor Management</h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {counselors.map((counselor) => (
                      <div key={counselor._id} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex items-start justify-between mb-3">
                          <div>
                            <h3 className="font-semibold text-gray-900">{counselor.name}</h3>
                            <p className="text-sm text-gray-500">{counselor.qualifications}</p>
                          </div>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            counselor.is_active
                              ? 'bg-green-100 text-green-700'
                              : 'bg-gray-100 text-gray-700'
                          }`}>
                            {counselor.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </div>
                        <div className="flex flex-wrap gap-2 mb-3">
                          {counselor.specialization.map((spec, idx) => (
                            <span
                              key={idx}
                              className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded-full"
                            >
                              {spec}
                            </span>
                          ))}
                        </div>
                        <div className="flex items-center justify-between text-sm text-gray-600">
                          <span>{counselor.experience_years} years experience</span>
                          <span className="flex items-center">
                            ⭐ {counselor.rating.toFixed(1)}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
};




