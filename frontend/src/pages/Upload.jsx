import { useState } from "react";
import { API_BASE_URL } from "../config";

function Upload() {
  // File upload state
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  // Handle file selection from input
  const handleFileChange = (event) => {
    const file = event.target.files[0];
    validateAndSetFile(file);
  };

  // Validate file type and set if valid
  const validateAndSetFile = (file) => {
    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".csv")) {
      setUploadStatus("Please select a CSV file only");
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
    setUploadStatus("");
  };

  // Handle drag events for visual feedback
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  // Handle file drop
  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  // Upload CSV file to backend API
  const handleUpload = async () => {
    if (!selectedFile) {
      setUploadStatus("Please select a file first");
      return;
    }

    setIsUploading(true);
    setUploadStatus("Uploading and processing your data...");

    try {
      // Create FormData to send the file
      const formData = new FormData();
      formData.append("file", selectedFile);

      // Make API call to backend
      const response = await fetch(`${API_BASE_URL}/upload`, {
        method: "POST",
        body: formData,
        credentials: "include", // Include cookies for session (needed for Django)
      });

      const data = await response.json();

      if (data.success) {
        setUploadStatus(data.message);
      } else {
        setUploadStatus(data.message || "Upload failed. Please try again.");
      }
    } catch (error) {
      console.error("Upload error:", error);
      setUploadStatus(
        "Error uploading file. Please check your connection and try again."
      );
    } finally {
      setIsUploading(false);
    }
  };

  // Clear selected file
  const clearFile = () => {
    setSelectedFile(null);
    setUploadStatus("");
  };

  // Download sample CSV file
  const handleDownloadSample = () => {
    const link = document.createElement("a");
    link.href = "/patient_appointments_upload.csv";
    link.download = "patient_appointments_upload.csv";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Open Kaggle dataset in new tab
  const handleKaggleLink = () => {
    window.open(
      "https://www.kaggle.com/datasets/joniarroba/noshowappointments",
      "_blank"
    );
  };

  return (
    <div className="max-w-7xl mx-auto">
      <div className="border-b-1 border-gray-200 py-12 mb-12">
        <h2 className="text-3xl font-bold text-gray-800">
          Upload Patient Data
        </h2>
        <p className="text-gray-600 mt-6">
          Upload your patient appointment data to generate no-show predictions
          and optimization insights.
        </p>
      </div>

      {/* File upload section with drag & drop */}
      <div className="bg-white rounded-lg shadow-lg p-8 mb-6">
        <h3 className="text-xl font-semibold mb-6 text-center">
          Select Your CSV File
        </h3>

        {/* Drag and drop zone */}
        <div
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            dragActive
              ? "border-blue-500 bg-blue-50"
              : selectedFile
              ? "border-green-500 bg-green-50"
              : "border-gray-300 hover:border-gray-400"
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          {selectedFile ? (
            <div className="space-y-4">
              <div className="text-green-600 text-4xl">📁</div>
              <div>
                <p className="text-lg font-medium text-green-700">
                  {selectedFile.name}
                </p>
                <p className="text-sm text-green-600">
                  {(selectedFile.size / 1024).toFixed(1)} KB
                </p>
              </div>
              <button
                onClick={clearFile}
                className="text-sm text-gray-500 hover:text-gray-700 border border-gray-300 px-4 py-1.5 rounded-full hover:bg-gray-100 transition-all"
              >
                Choose different file
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="text-gray-400 text-5xl">📤</div>
              <div>
                <p className="text-lg font-medium text-gray-500">
                  {dragActive
                    ? "Drop your CSV file here"
                    : "Drag & drop your CSV file here"}
                </p>
                <p className="text-sm text-gray-500 my-4">or</p>
                <label className="inline-flex items-center gap-2 px-6 py-2.5 bg-black text-white rounded-full hover:bg-slate-800 cursor-pointer transition-all shadow-md hover:shadow-lg">
                  <span>📂</span>
                  <span>Browse CSV Files</span>
                  <input
                    type="file"
                    accept=".csv"
                    onChange={handleFileChange}
                    className="hidden"
                  />
                </label>
              </div>
            </div>
          )}
        </div>

        {/* Upload button with loading state */}
        <div className="mt-8 text-center">
          <button
            onClick={handleUpload}
            disabled={!selectedFile || isUploading}
            className={`px-10 py-3.5 rounded-full font-semibold transition-all ${
              !selectedFile || isUploading
                ? "bg-slate-200 text-slate-400 cursor-not-allowed"
                : "bg-black text-white hover:bg-slate-800 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 cursor-pointer"
            }`}
          >
            {isUploading ? (
              <span className="flex items-center justify-center gap-2">
                <svg
                  className="animate-spin h-5 w-5 text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                <span>Processing...</span>
              </span>
            ) : (
              <span className="flex items-center justify-center gap-2">
                <span>🚀</span>
                <span>Upload & Process Data</span>
              </span>
            )}
          </button>
        </div>

        {/* Status message display */}
        {uploadStatus && (
          <div
            className={`mt-6 p-4 rounded-lg border ${
              uploadStatus.includes("successfully") ||
              uploadStatus.includes("success")
                ? "bg-green-50 text-green-700 border-green-200"
                : uploadStatus.includes("Please select") ||
                  uploadStatus.includes("CSV file only") ||
                  uploadStatus.includes("failed") ||
                  uploadStatus.includes("Error")
                ? "bg-red-50 text-red-700 border-red-200"
                : "bg-blue-50 text-blue-700 border-blue-200"
            }`}
          >
            <div className="flex items-center">
              <span>{uploadStatus}</span>
            </div>
          </div>
        )}
      </div>

      {/* CSV format documentation and download section */}
      <div className="bg-white rounded-lg shadow-lg p-8">
        <h3 className="text-xl font-semibold mb-4 text-gray-800">
          Expected CSV Format
        </h3>
        <p className="text-gray-600 mb-4">
          Your CSV file should contain the following columns in this exact
          order:
        </p>

        <div className="bg-gray-50 rounded-lg p-4 mb-6 overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="border-b border-gray-300">
              <tr>
                <th className="text-left py-2 px-3 font-semibold text-gray-700">
                  Column Name
                </th>
                <th className="text-left py-2 px-3 font-semibold text-gray-700">
                  Description
                </th>
                <th className="text-left py-2 px-3 font-semibold text-gray-700">
                  Example
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              <tr>
                <td className="py-2 px-3 font-mono text-blue-600">PatientId</td>
                <td className="py-2 px-3 text-gray-600">
                  Unique patient identifier
                </td>
                <td className="py-2 px-3 text-gray-500">29872499824296</td>
              </tr>
              <tr>
                <td className="py-2 px-3 font-mono text-blue-600">
                  AppointmentID
                </td>
                <td className="py-2 px-3 text-gray-600">
                  Unique appointment ID
                </td>
                <td className="py-2 px-3 text-gray-500">5642903</td>
              </tr>
              <tr>
                <td className="py-2 px-3 font-mono text-blue-600">Gender</td>
                <td className="py-2 px-3 text-gray-600">
                  Patient gender (M/F)
                </td>
                <td className="py-2 px-3 text-gray-500">F</td>
              </tr>
              <tr>
                <td className="py-2 px-3 font-mono text-blue-600">
                  ScheduledDay
                </td>
                <td className="py-2 px-3 text-gray-600">
                  When appointment was scheduled
                </td>
                <td className="py-2 px-3 text-gray-500">
                  2016-04-29T18:38:08Z
                </td>
              </tr>
              <tr>
                <td className="py-2 px-3 font-mono text-blue-600">
                  AppointmentDay
                </td>
                <td className="py-2 px-3 text-gray-600">
                  Actual appointment date
                </td>
                <td className="py-2 px-3 text-gray-500">
                  2016-04-29T00:00:00Z
                </td>
              </tr>
              <tr>
                <td className="py-2 px-3 font-mono text-blue-600">Age</td>
                <td className="py-2 px-3 text-gray-600">
                  Patient age in years
                </td>
                <td className="py-2 px-3 text-gray-500">62</td>
              </tr>
              <tr>
                <td className="py-2 px-3 font-mono text-blue-600">
                  Neighbourhood
                </td>
                <td className="py-2 px-3 text-gray-600">
                  Patient neighborhood
                </td>
                <td className="py-2 px-3 text-gray-500">JARDIM DA PENHA</td>
              </tr>
              <tr>
                <td className="py-2 px-3 font-mono text-blue-600">
                  Scholarship
                </td>
                <td className="py-2 px-3 text-gray-600">
                  Has scholarship (0/1)
                </td>
                <td className="py-2 px-3 text-gray-500">0</td>
              </tr>
              <tr>
                <td className="py-2 px-3 font-mono text-blue-600">
                  Hipertension
                </td>
                <td className="py-2 px-3 text-gray-600">
                  Has hypertension (0/1)
                </td>
                <td className="py-2 px-3 text-gray-500">1</td>
              </tr>
              <tr>
                <td className="py-2 px-3 font-mono text-blue-600">Diabetes</td>
                <td className="py-2 px-3 text-gray-600">Has diabetes (0/1)</td>
                <td className="py-2 px-3 text-gray-500">0</td>
              </tr>
              <tr>
                <td className="py-2 px-3 font-mono text-blue-600">
                  Alcoholism
                </td>
                <td className="py-2 px-3 text-gray-600">
                  Has alcoholism (0/1)
                </td>
                <td className="py-2 px-3 text-gray-500">0</td>
              </tr>
              <tr>
                <td className="py-2 px-3 font-mono text-blue-600">Handcap</td>
                <td className="py-2 px-3 text-gray-600">
                  Handicap level (0-4)
                </td>
                <td className="py-2 px-3 text-gray-500">0</td>
              </tr>
              <tr>
                <td className="py-2 px-3 font-mono text-blue-600">
                  SMS_received
                </td>
                <td className="py-2 px-3 text-gray-600">
                  SMS reminder sent (0/1)
                </td>
                <td className="py-2 px-3 text-gray-500">0</td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Download sample and Kaggle link buttons */}
        <div className="flex flex-col sm:flex-row gap-4 items-center justify-center">
          <button
            onClick={handleDownloadSample}
            className="px-6 py-3 border-2 border-slate-300 text-black rounded-full hover:bg-slate-100 transition-all font-medium flex items-center gap-2 cursor-pointer"
          >
            <span>📥</span>
            <span>Download Sample CSV</span>
          </button>

          <span className="text-slate-300">or</span>

          <button
            onClick={handleKaggleLink}
            className="px-6 py-3 border-2 border-slate-300 text-black rounded-full hover:bg-slate-100 transition-all font-medium flex items-center gap-2 cursor-pointer"
          >
            <span>🔗</span>
            <span>Get from Kaggle</span>
          </button>
        </div>
      </div>
    </div>
  );
}

export default Upload;
