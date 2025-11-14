import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Navbar } from '../components/Navbar';
import { sessionAPI, appointmentAPI } from '../utils/api';
import { MessageCircle, Calendar, Clock, TrendingUp, Activity } from 'lucide-react';

export const DashboardPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [recentSessions, setRecentSessions] = useState([]);
  const [upcomingAppointments, setUpcomingAppointments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const [sessionsRes, appointmentsRes] = await Promise.all([
        sessionAPI.getMySessions(5),
        appointmentAPI.getMyAppointments()
      ]);

      setRecentSessions(sessionsRes.data);
      setUpcomingAppointments(
        appointmentsRes.data.filter(apt => 
          apt.status === 'scheduled' && new Date(apt.scheduled_time) > new Date()
        )
      );
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
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
          {/* Welcome Section */}
          <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl shadow-lg p-8 mb-8 text-white">
            <h1 className="text-3xl font-bold mb-2">Welcome back, {user?.full_name}!</h1>
            <p className="text-blue-100">How are you feeling today? I'm here to help.</p>
          </div>

          {/* Quick Actions */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <button
              onClick={() => navigate('/chat')}
              className="bg-white p-6 rounded-xl shadow-md hover:shadow-lg transition group"
            >
              <div className="flex items-center space-x-4">
                <div className="bg-blue-100 p-3 rounded-lg group-hover:bg-blue-200 transition">
                  <MessageCircle className="w-8 h-8 text-blue-600" />
                </div>
                <div className="text-left">
                  <h3 className="font-semibold text-gray-900">Start Chat Session</h3>
                  <p className="text-sm text-gray-500">Talk to your AI assistant</p>
                </div>
              </div>
            </button>

            <button
              onClick={() => navigate('/book-counselor')}
              className="bg-white p-6 rounded-xl shadow-md hover:shadow-lg transition group"
            >
              <div className="flex items-center space-x-4">
                <div className="bg-green-100 p-3 rounded-lg group-hover:bg-green-200 transition">
                  <Calendar className="w-8 h-8 text-green-600" />
                </div>
                <div className="text-left">
                  <h3 className="font-semibold text-gray-900">Book Counselor</h3>
                  <p className="text-sm text-gray-500">Schedule an appointment</p>
                </div>
              </div>
            </button>

            <button
              onClick={() => navigate('/sessions')}
              className="bg-white p-6 rounded-xl shadow-md hover:shadow-lg transition group"
            >
              <div className="flex items-center space-x-4">
                <div className="bg-purple-100 p-3 rounded-lg group-hover:bg-purple-200 transition">
                  <Activity className="w-8 h-8 text-purple-600" />
                </div>
                <div className="text-left">
                  <h3 className="font-semibold text-gray-900">View History</h3>
                  <p className="text-sm text-gray-500">See past sessions</p>
                </div>
              </div>
            </button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Recent Sessions */}
            <div className="bg-white rounded-xl shadow-md p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-gray-900">Recent Sessions</h2>
                <Clock className="w-5 h-5 text-gray-400" />
              </div>

              {recentSessions.length === 0 ? (
                <div className="text-center py-8">
                  <MessageCircle className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500">No sessions yet</p>
                  <button
                    onClick={() => navigate('/chat')}
                    className="mt-4 text-blue-600 hover:text-blue-700 font-medium"
                  >
                    Start your first session
                  </button>
                </div>
              ) : (
                <div className="space-y-4">
                  {recentSessions.map((session) => (
                    <div
                      key={session._id}
                      className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition cursor-pointer"
                      onClick={() => navigate(`/sessions/${session.session_id}`)}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-gray-900">
                          Session {session.session_id.slice(0, 8)}...
                        </span>
                        <span className="text-xs text-gray-500">
                          {formatDate(session.start_time)}
                        </span>
                      </div>
                      {session.overall_sentiment && (
                        <div className="flex items-center space-x-2">
                          <TrendingUp className="w-4 h-4 text-green-500" />
                          <span className="text-sm text-gray-600 capitalize">
                            {session.overall_sentiment}
                          </span>
                        </div>
                      )}
                      {session.duration_minutes && (
                        <p className="text-xs text-gray-500 mt-1">
                          Duration: {session.duration_minutes} minutes
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Upcoming Appointments */}
            <div className="bg-white rounded-xl shadow-md p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-gray-900">Upcoming Appointments</h2>
                <Calendar className="w-5 h-5 text-gray-400" />
              </div>

              {upcomingAppointments.length === 0 ? (
                <div className="text-center py-8">
                  <Calendar className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500">No upcoming appointments</p>
                  <button
                    onClick={() => navigate('/book-counselor')}
                    className="mt-4 text-blue-600 hover:text-blue-700 font-medium"
                  >
                    Book an appointment
                  </button>
                </div>
              ) : (
                <div className="space-y-4">
                  {upcomingAppointments.map((appointment) => (
                    <div
                      key={appointment._id}
                      className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-gray-900">
                          Dr. {appointment.counselor_id}
                        </span>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          appointment.meeting_type === 'video'
                            ? 'bg-blue-100 text-blue-700'
                            : 'bg-green-100 text-green-700'
                        }`}>
                          {appointment.meeting_type}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600">
                        {formatDate(appointment.scheduled_time)}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        Duration: {appointment.duration_minutes} minutes
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
};