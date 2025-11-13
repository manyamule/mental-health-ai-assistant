import { useState } from 'react';
import { Upload, FileText, X, CheckCircle } from 'lucide-react';
import axios from 'axios';
import { API_BASE_URL } from '../config';

export const DocumentUpload = ({ onDocumentProcessed, onSkip }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
      setUploadStatus(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setUploadStatus(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await axios.post(`${API_BASE_URL}/upload_document/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setUploadStatus({ type: 'success', message: 'Document processed successfully!' });
      setTimeout(() => {
        onDocumentProcessed(response.data.document_info);
      }, 1500);
    } catch (error) {
      setUploadStatus({ 
        type: 'error', 
        message: error.response?.data?.error || 'Failed to upload document' 
      });
    } finally {
      setUploading(false);
    }
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
    setUploadStatus(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full">
        <div className="text-center mb-6">
          <div className="mx-auto w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
            <FileText className="w-8 h-8 text-blue-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Medical Document Upload</h2>
          <p className="text-gray-600 text-sm">
            Upload your medical document for better context (optional)
          </p>
        </div>

        {!selectedFile ? (
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition cursor-pointer">
            <input
              type="file"
              id="file-upload"
              className="hidden"
              accept=".pdf,.jpg,.jpeg,.png,.tiff"
              onChange={handleFileSelect}
            />
            <label htmlFor="file-upload" className="cursor-pointer">
              <Upload className="mx-auto w-12 h-12 text-gray-400 mb-4" />
              <p className="text-gray-600 mb-2">Click to upload or drag and drop</p>
              <p className="text-gray-400 text-xs">PDF, JPG, PNG, TIFF (MAX. 10MB)</p>
            </label>
          </div>
        ) : (
          <div className="bg-gray-50 rounded-lg p-4 mb-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <FileText className="w-8 h-8 text-blue-600" />
                <div>
                  <p className="text-sm font-medium text-gray-800">{selectedFile.name}</p>
                  <p className="text-xs text-gray-500">
                    {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              </div>
              <button
                onClick={handleRemoveFile}
                className="text-red-500 hover:text-red-700"
                disabled={uploading}
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>
        )}

        {uploadStatus && (
          <div className={`p-3 rounded-lg mb-4 flex items-center space-x-2 ${
            uploadStatus.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
          }`}>
            {uploadStatus.type === 'success' && <CheckCircle className="w-5 h-5" />}
            <p className="text-sm">{uploadStatus.message}</p>
          </div>
        )}

        <div className="space-y-3">
          <button
            onClick={handleUpload}
            disabled={!selectedFile || uploading}
            className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition font-medium"
          >
            {uploading ? 'Processing...' : 'Upload & Continue'}
          </button>
          
          <button
            onClick={onSkip}
            disabled={uploading}
            className="w-full bg-gray-200 text-gray-700 py-3 rounded-lg hover:bg-gray-300 transition font-medium"
          >
            Skip for Now
          </button>
        </div>
      </div>
    </div>
  );
};