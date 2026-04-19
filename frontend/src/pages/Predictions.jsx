import { useState, useEffect } from "react";
import { API_BASE_URL } from "../config";

function PredictionsFullView() {
  const [patients, setPatients] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // LIME explanation modal state
  const [explanation, setExplanation] = useState(null);
  const [explanationLoading, setExplanationLoading] = useState(false);
  const [explanationError, setExplanationError] = useState(null);
  const [explanationFor, setExplanationFor] = useState(null);

  // Fetch predictions from API on component mount
  useEffect(() => {
    const fetchPredictions = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await fetch(`${API_BASE_URL}/predictions`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          credentials: "include", // Include cookies for session
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || "Failed to fetch predictions");
        }

        const data = await response.json();
        setPatients(data);
      } catch (err) {
        console.error("Predictions error:", err);
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };

    fetchPredictions();
  }, []);

  // Clear all patient data from backend
  const handleClearData = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/clear`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
      });

      const data = await response.json();

      if (data.success) {
        setPatients([]);
        setError(null);
      } else {
        setError(data.message || "Failed to clear data");
      }
    } catch (error) {
      console.error("Clear data error:", error);
      setError("Error clearing data. Please try again.");
    }
  };

  // Fetch a LIME explanation for a single appointment and open the modal
  const handleExplain = async (patient) => {
    setExplanationFor(patient);
    setExplanation(null);
    setExplanationError(null);
    setExplanationLoading(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/predictions/${patient.appointmentId}/explain`,
        {
          method: "GET",
          credentials: "include",
        }
      );
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.error ||
            `Failed to load explanation (HTTP ${response.status})`
        );
      }
      const data = await response.json();
      setExplanation(data);
    } catch (err) {
      console.error("Explain error:", err);
      setExplanationError(err.message);
    } finally {
      setExplanationLoading(false);
    }
  };

  const closeExplanation = () => {
    setExplanationFor(null);
    setExplanation(null);
    setExplanationError(null);
    setExplanationLoading(false);
  };

  // Filter and sort state
  const [filterRisk, setFilterRisk] = useState("all");
  const [sortBy, setSortBy] = useState("probability");

  // Filter patients by risk level
  const filteredPatients = patients.filter(
    (patient) =>
      filterRisk === "all" ||
      patient.riskLevel.toLowerCase() === filterRisk.toLowerCase()
  );

  // Sort patients by selected criteria
  const sortedPatients = [...filteredPatients].sort((a, b) => {
    switch (sortBy) {
      case "probability":
        return b.noShowProbability - a.noShowProbability;
      case "name":
        return a.name.localeCompare(b.name);
      case "date":
        return new Date(a.appointmentDate) - new Date(b.appointmentDate);
      default:
        return 0;
    }
  });

  // Helper function: assign color classes based on risk level
  const getRiskColor = (risk) => {
    switch (risk) {
      case "High":
        return "text-red-600 bg-red-100";
      case "Medium":
        return "text-yellow-600 bg-yellow-100";
      case "Low":
        return "text-green-600 bg-green-100";
      default:
        return "text-gray-600 bg-gray-100";
    }
  };

  // Helper function: assign color based on probability threshold
  const getProbabilityColor = (probability) => {
    if (probability >= 0.6) return "text-red-600 font-bold";
    if (probability >= 0.3) return "text-yellow-600 font-semibold";
    return "text-green-600";
  };

  return (
    <div className="max-w-7xl mx-auto px-4">
      <div className="border-b-1 border-gray-200 py-12 mb-12">
        <h2 className="text-3xl font-bold text-gray-800">
          Patient Predictions
        </h2>
        <p className="text-gray-600 mt-6">
          View no-show risk predictions for each patient, filter by risk level,
          and identify high-risk appointments.
        </p>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="bg-white rounded-lg shadow p-8 text-center mb-6">
          <div className="flex items-center justify-center gap-2">
            <svg
              className="animate-spin h-5 w-5 text-gray-400"
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
            <span className="text-gray-600">Loading predictions...</span>
          </div>
        </div>
      )}

      {/* Error state */}
      {error && !isLoading && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 mb-6">
          <div className="flex items-center gap-2 text-red-700">
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !error && patients.length === 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 mb-6">
          <div className="flex items-center gap-2 text-yellow-700">
            <span>No patient data available.</span>
          </div>
        </div>
      )}

      {/* Risk summary cards: Total, High, Medium, Low */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="text-sm font-medium text-gray-500">Total Patients</h3>
          <p className="text-2xl font-bold text-gray-900">{patients.length}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="text-sm font-medium text-gray-500">High Risk</h3>
          <p className="text-2xl font-bold text-red-600">
            {patients.filter((p) => p.riskLevel === "High").length}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="text-sm font-medium text-gray-500">Medium Risk</h3>
          <p className="text-2xl font-bold text-yellow-600">
            {patients.filter((p) => p.riskLevel === "Medium").length}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="text-sm font-medium text-gray-500">Low Risk</h3>
          <p className="text-2xl font-bold text-green-600">
            {patients.filter((p) => p.riskLevel === "Low").length}
          </p>
        </div>
      </div>

      {/* Filter and sort controls with export button */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex flex-wrap gap-4 items-center justify-between">
          <div className="flex gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Filter by Risk:
              </label>
              <select
                value={filterRisk}
                onChange={(e) => setFilterRisk(e.target.value)}
                className="border border-slate-300 rounded-full px-4 py-1.5 text-sm outline-none"
              >
                <option value="all">All Risk Levels</option>
                <option value="high">High Risk</option>
                <option value="medium">Medium Risk</option>
                <option value="low">Low Risk</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Sort by:
              </label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="border border-slate-300 rounded-full px-4 py-1.5 text-sm focus:outline-none"
              >
                <option value="probability">No-Show Probability</option>
                <option value="name">Patient ID</option>
                <option value="date">Appointment Date</option>
              </select>
            </div>
          </div>

          <div>
            <button
              onClick={handleClearData}
              disabled={patients.length === 0}
              className={`px-3 py-1 border-2 border-slate-300 rounded-full transition-all text-xs flex items-center gap-2 ${
                patients.length === 0
                  ? "text-slate-400 cursor-not-allowed opacity-60"
                  : " border-red-300 hover:bg-slate-100 transition-all cursor-pointer"
              }`}
            >
              <span>🗑️</span>
              <span>Clear All Data</span>
            </button>
          </div>
        </div>
      </div>

      {/* Patient data table with all CSV columns and predictions */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Patient Info
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Appointment Details
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Location
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Medical Conditions
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Socioeconomic
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  History
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Prediction
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {sortedPatients.map((patient) => (
                <tr key={patient.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 whitespace-nowrap">
                    <div className="text-xs">
                      <div className="font-medium text-gray-900">
                        ID: {patient.id}
                      </div>
                      <div className="text-gray-500">
                        {patient.age} yrs, {patient.gender}
                      </div>
                      <div className="text-gray-400 text-xs">
                        Appt #{patient.appointmentId}
                      </div>
                    </div>
                  </td>

                  <td className="px-4 py-3">
                    <div className="text-xs">
                      <div className="font-medium">
                        {new Date(patient.appointmentDate).toLocaleDateString()}
                      </div>
                      <div className="text-gray-500">
                        Scheduled:{" "}
                        {new Date(patient.scheduledDay).toLocaleDateString()}
                      </div>
                      <div className="text-gray-500">
                        Wait:{" "}
                        {Math.abs(
                          Math.floor(
                            (new Date(patient.appointmentDate) -
                              new Date(patient.scheduledDay)) /
                              (1000 * 60 * 60 * 24)
                          )
                        )}{" "}
                        days
                      </div>
                    </div>
                  </td>

                  <td className="px-4 py-3">
                    <div className="text-xs text-gray-700">
                      {patient.neighbourhood}
                    </div>
                  </td>

                  <td className="px-4 py-3">
                    <div className="text-xs space-y-1">
                      <div>
                        Hypertension:{" "}
                        <span
                          className={
                            patient.hipertension
                              ? "text-red-600"
                              : "text-gray-400"
                          }
                        >
                          {patient.hipertension ? "Yes" : "No"}
                        </span>
                      </div>
                      <div>
                        Diabetes:{" "}
                        <span
                          className={
                            patient.diabetes ? "text-red-600" : "text-gray-400"
                          }
                        >
                          {patient.diabetes ? "Yes" : "No"}
                        </span>
                      </div>
                      <div>
                        Alcoholism:{" "}
                        <span
                          className={
                            patient.alcoholism
                              ? "text-red-600"
                              : "text-gray-400"
                          }
                        >
                          {patient.alcoholism ? "Yes" : "No"}
                        </span>
                      </div>
                      <div>
                        Handicap:{" "}
                        <span className="text-gray-700">
                          {patient.handcap > 0
                            ? `Level ${patient.handcap}`
                            : "No"}
                        </span>
                      </div>
                    </div>
                  </td>

                  <td className="px-4 py-3">
                    <div className="text-xs">
                      <div>
                        Scholarship:{" "}
                        <span
                          className={
                            patient.scholarship
                              ? "text-blue-600"
                              : "text-gray-400"
                          }
                        >
                          {patient.scholarship ? "Yes" : "No"}
                        </span>
                      </div>
                      <div className="mt-1">
                        SMS Sent:{" "}
                        <span
                          className={
                            patient.smsReceived
                              ? "text-green-600"
                              : "text-gray-400"
                          }
                        >
                          {patient.smsReceived ? "Yes" : "No"}
                        </span>
                      </div>
                    </div>
                  </td>

                  <td className="px-4 py-3">
                    <div className="text-xs">
                      <div>
                        Previous No-Shows:{" "}
                        <span
                          className={
                            patient.previousNoShows > 0
                              ? "text-red-600 font-semibold"
                              : "text-gray-400"
                          }
                        >
                          {patient.previousNoShows}
                        </span>
                      </div>
                    </div>
                  </td>

                  <td className="px-4 py-3">
                    <div className="text-xs">
                      <div
                        className={`font-semibold ${getProbabilityColor(
                          patient.noShowProbability
                        )}`}
                      >
                        {(patient.noShowProbability * 100).toFixed(1)}%
                      </div>
                      <span
                        className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getRiskColor(
                          patient.riskLevel
                        )}`}
                      >
                        {patient.riskLevel}
                      </span>
                    </div>
                  </td>

                  <td className="px-4 py-3 whitespace-nowrap text-xs font-medium">
                    <button
                      onClick={() => handleExplain(patient)}
                      className="px-3 py-1 border border-indigo-300 text-indigo-700 rounded-full transition-all mr-2 hover:bg-indigo-50 cursor-pointer"
                    >
                      Why?
                    </button>
                    <button className="px-3 py-1 border border-slate-300 text-slate-400 rounded-full transition-all mr-2 cursor-not-allowed opacity-60">
                      📧 Remind
                    </button>
                    <button className="px-3 py-1 border border-slate-300 text-slate-400 rounded-full transition-all cursor-not-allowed opacity-60">
                      📅 Reschedule
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* LIME explanation modal */}
      {explanationFor && (
        <div
          className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4"
          onClick={closeExplanation}
        >
          <div
            className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[85vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal header */}
            <div className="border-b border-gray-200 px-6 py-4 flex items-start justify-between">
              <div>
                <h3 className="text-lg font-bold text-gray-900">
                  Why this prediction?
                </h3>
                <p className="text-xs text-gray-500 mt-1">
                  Patient ID {explanationFor.id} · Appointment #
                  {explanationFor.appointmentId}
                </p>
              </div>
              <button
                onClick={closeExplanation}
                className="text-gray-400 hover:text-gray-700 text-2xl leading-none cursor-pointer"
                aria-label="Close"
              >
                ×
              </button>
            </div>

            {/* Modal body */}
            <div className="px-6 py-5">
              {explanationLoading && (
                <div className="text-center py-8">
                  <div className="flex items-center justify-center gap-2">
                    <svg
                      className="animate-spin h-5 w-5 text-gray-400"
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
                    <span className="text-gray-600 text-sm">
                      Computing explanation…
                    </span>
                  </div>
                  <p className="text-xs text-gray-400 mt-2">
                    This can take a few seconds the first time.
                  </p>
                </div>
              )}

              {explanationError && !explanationLoading && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <p className="text-red-700 text-sm">{explanationError}</p>
                </div>
              )}

              {explanation && !explanationLoading && !explanationError && (
                <>
                  <div className="mb-4">
                    <p className="text-sm text-gray-600">
                      Predicted no-show probability:
                    </p>
                    <p
                      className={`text-3xl font-bold ${getProbabilityColor(
                        explanation.noShowProbability
                      )}`}
                    >
                      {(explanation.noShowProbability * 100).toFixed(1)}%
                    </p>
                  </div>

                  <div className="border-t border-gray-100 pt-4">
                    <p className="text-sm font-semibold text-gray-700 mb-1">
                      Top contributing factors
                    </p>
                    <p className="text-xs text-gray-500 mb-4">
                      Red bars push toward <strong>No-Show</strong>. Green bars
                      push toward <strong>Show</strong>. Bar length reflects
                      relative impact.
                    </p>

                    {(() => {
                      const maxAbs = Math.max(
                        ...explanation.topFeatures.map((f) =>
                          Math.abs(f.weight)
                        ),
                        1e-9
                      );
                      return (
                        <ul className="space-y-2">
                          {explanation.topFeatures.map((f, idx) => {
                            const widthPct = (Math.abs(f.weight) / maxAbs) * 100;
                            const isNoShow = f.direction === "noshow";
                            return (
                              <li key={idx} className="text-xs">
                                <div className="flex items-center justify-between mb-1">
                                  <span
                                    className="text-gray-800 font-mono truncate pr-2"
                                    title={f.feature}
                                  >
                                    {f.feature}
                                  </span>
                                  <span
                                    className={
                                      isNoShow
                                        ? "text-red-600 font-semibold"
                                        : "text-green-600 font-semibold"
                                    }
                                  >
                                    {f.weight > 0 ? "+" : ""}
                                    {f.weight.toFixed(3)}
                                  </span>
                                </div>
                                <div className="w-full bg-gray-100 rounded h-2 overflow-hidden">
                                  <div
                                    className={`h-2 rounded ${
                                      isNoShow ? "bg-red-500" : "bg-green-500"
                                    }`}
                                    style={{ width: `${widthPct}%` }}
                                  />
                                </div>
                              </li>
                            );
                          })}
                        </ul>
                      );
                    })()}
                  </div>
                </>
              )}
            </div>

            {/* Modal footer */}
            <div className="border-t border-gray-200 px-6 py-3 bg-gray-50 rounded-b-lg flex justify-end">
              <button
                onClick={closeExplanation}
                className="px-4 py-1.5 text-sm border border-slate-300 rounded-full hover:bg-slate-100 cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default PredictionsFullView;
