import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Navbar } from '../components/Navbar';
import { appointmentAPI } from '../utils/api';
import { Calendar, Clock, Video, Phone, MessageSquare, Star, CheckCircle } from 'lucide-react';

export const BookCounselorPage = () => {
  const [counselors, setCounselors] = useState([]);
  const [selectedCounselor, setSelectedCounselor] = useState(null);
  const [appointmentData, setAppointmentData] = useState({
    scheduled_time: '',
    duration_minutes: 60,
    meeting_type: 'video',
    notes: ''
  });
  const [loading, setLoading] = useState(true);
  const [booking, setBooking] = useState(false);
  const [success, setSuccess] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    loadCounselors();
  }, []);

  const loadCounselors = async () => {
    try {
      const response = await appointmentAPI.getCounselors();
      setCounselors(response.data);
    } catch (error) {
      console.error('Failed to load counselors:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleBookAppointment = async () => {
    if (!selectedCounselor || !appointmentData.scheduled_time) {
      alert('Please select a counselor and appointment time');
      return;
    }

    setBooking(true);
    try {
      await appointmentAPI.bookAppointment({
        counselor_id: selectedCounselor._id,
        ...appointmentData
      });
      setSuccess(true);
      setTimeout(() => {
        navigate('/dashboard');
      }, 2000);
    } catch (error) {
      console.error('Failed to book appointment:', error);
      alert('Failed to book appointment. Please try again.');
    } finally {
      setBooking(false);
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

  if (success) {
    return (
      <>
        <Navbar />
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="bg-white p-8 rounded-2xl shadow-xl text-center max-w-md">
            <div className="bg-green-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="w-10 h-10 text-green-600" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Appointment Booked!</h2>
            <p className="text-gray-600 mb-6">
              Your appointment has been successfully scheduled. You'll receive a confirmation email shortly.
            </p>
            <button
              onClick={() => navigate('/dashboard')}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition"
            >
              Back to Dashboard
            </button>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-8">Book a Counselor</h1>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Counselors List */}
            <div className="lg:col-span-2 space-y-4">
              {counselors.map((counselor) => (
                <div
                  key={counselor._id}
                  className={`bg-white rounded-xl shadow-md p-6 cursor-pointer transition ${
                    selectedCounselor?._id === counselor._id
                      ? 'ring-2 ring-blue-500'
                      : 'hover:shadow-lg'
                  }`}
                  onClick={() => setSelectedCounselor(counselor)}
                >
                  <div className="flex items-start space-x-4">
                    <div className="bg-blue-100 w-16 h-16 rounded-full flex items-center justify-center flex-shrink-0">
                      <span className="text-2xl font-bold text-blue-600">
                        {counselor.name.charAt(0)}
                      </span>
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="text-xl font-semibold text-gray-900">
                          {counselor.name}
                        </h3>
                        <div className="flex items-center space-x-1">
                          <Star className="w-5 h-5 text-yellow-400 fill-current" />
                          <span className="text-sm font-medium text-gray-700">
                            {counselor.rating.toFixed(1)}
                          </span>
                        </div>
                      </div>
                      <p className="text-sm text-gray-600 mb-2">{counselor.qualifications}</p>
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
                      <p className="text-sm text-gray-600 mb-2">{counselor.bio}</p>
                      <p className="text-xs text-gray-500">
                        {counselor.experience_years} years of experience
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Booking Form */}
            <div className="lg:col-span-1">
              <div className="bg-white rounded-xl shadow-md p-6 sticky top-8">
                <h2 className="text-xl font-bold text-gray-900 mb-4">Book Appointment</h2>

                {!selectedCounselor ? (
                  <p className="text-gray-500 text-center py-8">
                    Select a counselor to continue
                  </p>
                ) : (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Date & Time
                      </label>
                      <input
                        type="datetime-local"
                        value={appointmentData.scheduled_time}
                        onChange={(e) =>
                          setAppointmentData({ ...appointmentData, scheduled_time: e.target.value })
                        }
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        min={new Date().toISOString().slice(0, 16)}
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Duration
                      </label>
                      <select
                        value={appointmentData.duration_minutes}
                        onChange={(e) =>
                          setAppointmentData({
                            ...appointmentData,
                            duration_minutes: parseInt(e.target.value)
                          })
                        }
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      >
                        <option value={30}>30 minutes</option>
                        <option value={60}>60 minutes</option>
                        <option value={90}>90 minutes</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Meeting Type
                      </label>
                      <div className="grid grid-cols-3 gap-2">
                        <button
                          type="button"
                          onClick={() =>
                            setAppointmentData({ ...appointmentData, meeting_type: 'video' })
                          }
                          className={`p-3 rounded-lg border-2 transition ${
                            appointmentData.meeting_type === 'video'
                              ? 'border-blue-500 bg-blue-50'
                              : 'border-gray-200'
                          }`}
                        >
                          <Video className="w-6 h-6 mx-auto mb-1" />
                          <span className="text-xs">Video</span>
                        </button>
                        <button
                          type="button"
                          onClick={() =>
                            setAppointmentData({ ...appointmentData, meeting_type: 'audio' })
                          }
                          className={`p-3 rounded-lg border-2 transition ${
                            appointmentData.meeting_type === 'audio'
                              ? 'border-blue-500 bg-blue-50'
                              : 'border-gray-200'
                          }`}
                        >
                          <Phone className="w-6 h-6 mx-auto mb-1" />
                          <span className="text-xs">Audio</span>
                        </button>
                        <button
                          type="button"
                          onClick={() =>
                            setAppointmentData({ ...appointmentData, meeting_type: 'chat' })
                          }
                          className={`p-3 rounded-lg border-2 transition ${
                            appointmentData.meeting_type === 'chat'
                              ? 'border-blue-500 bg-blue-50'
                              : 'border-gray-200'
                          }`}
                        >
                          <MessageSquare className="w-6 h-6 mx-auto mb-1" />
                          <span className="text-xs">Chat</span>
                        </button>
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Notes (Optional)
                      </label>
                      <textarea
                        value={appointmentData.notes}
                        onChange={(e) =>
                          setAppointmentData({ ...appointmentData, notes: e.target.value })
                        }
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        rows={3}
                        placeholder="Any specific concerns or topics you'd like to discuss..."
                      />
                    </div>

                    <button
                      onClick={handleBookAppointment}
                      disabled={booking}
                      className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 disabled:bg-gray-300 transition font-medium"
                    >
                      {booking ? 'Booking...' : 'Confirm Booking'}
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};