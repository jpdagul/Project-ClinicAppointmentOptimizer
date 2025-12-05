import { useState } from "react";
import { API_BASE_URL } from "../config";

function Simulation() {
  // Simulation parameter state
  const [parameters, setParameters] = useState({
    doctors: 0,
    slotsPerDay: 0,
    overbookingPercentage: 0,
    averageAppointmentTime: 0,
    clinicHours: 0,
  });

  // Results state and loading indicator
  const [simulationResults, setSimulationResults] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState(null);

  // Update parameter values from sliders
  const handleParameterChange = (key, value) => {
    setParameters((prev) => ({
      ...prev,
      [key]: parseInt(value),
    }));
  };

  // Run simulation via API
  const runSimulation = async () => {
    setIsRunning(true);
    setError(null);
    setSimulationResults(null);

    try {
      const response = await fetch(`${API_BASE_URL}/simulation/run`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify(parameters),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Simulation failed");
      }

      const data = await response.json();
      setSimulationResults(data);
    } catch (err) {
      console.error("Simulation error:", err);
      setError(err.message);
    } finally {
      setIsRunning(false);
    }
  };

  // Helper function: assign color based on utilization threshold
  const getUtilizationColor = (utilization) => {
    if (utilization >= 90) return "text-red-600";
    if (utilization >= 80) return "text-yellow-600";
    return "text-green-600";
  };

  // Helper function: assign color based on wait time threshold
  const getWaitTimeColor = (waitTime) => {
    if (waitTime >= 45) return "text-red-600";
    if (waitTime >= 30) return "text-yellow-600";
    return "text-green-600";
  };

  return (
    <div className="max-w-7xl mx-auto">
      <div className="border-b-1 border-gray-200 py-12 mb-12">
        <h2 className="text-3xl font-bold text-gray-800">
          Clinic Simulation & Optimization
        </h2>
        <p className="text-gray-600 mt-6">
          Adjust clinic parameters and run simulations to find the optimal
          scheduling strategy for your practice.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left section: Parameter sliders and run button */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Clinic Parameters</h3>

          <div className="space-y-6">
            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="text-sm font-medium text-gray-700">
                  Number of Doctors
                </label>
                <span className="text-sm font-semibold text-black bg-slate-200 px-2 py-0.5 rounded-full">
                  {parameters.doctors}
                </span>
              </div>
              <input
                type="range"
                min="1"
                max="10"
                value={parameters.doctors}
                onChange={(e) =>
                  handleParameterChange("doctors", e.target.value)
                }
                className="w-full h-2 bg-slate-200 rounded-full appearance-none cursor-grab accent-black"
              />
            </div>

            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="text-sm font-medium text-gray-700">
                  Appointment Slots per Day
                </label>
                <span className="text-sm font-semibold text-black bg-slate-200 px-2 py-0.5 rounded-full">
                  {parameters.slotsPerDay}
                </span>
              </div>
              <input
                type="range"
                min="10"
                max="50"
                value={parameters.slotsPerDay}
                onChange={(e) =>
                  handleParameterChange("slotsPerDay", e.target.value)
                }
                className="w-full h-2 bg-slate-200 rounded-full appearance-none cursor-grab accent-black"
              />
            </div>

            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="text-sm font-medium text-gray-700">
                  Overbooking Percentage
                </label>
                <span className="text-sm font-semibold text-black bg-slate-200 px-2 py-0.5 rounded-full">
                  {parameters.overbookingPercentage}%
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="30"
                value={parameters.overbookingPercentage}
                onChange={(e) =>
                  handleParameterChange("overbookingPercentage", e.target.value)
                }
                className="w-full h-2 bg-slate-200 rounded-full appearance-none cursor-grab accent-black"
              />
            </div>

            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="text-sm font-medium text-gray-700">
                  Average Appointment Time
                </label>
                <span className="text-sm font-semibold text-black bg-slate-200 px-2 py-0.5 rounded-full">
                  {parameters.averageAppointmentTime} min
                </span>
              </div>
              <input
                type="range"
                min="15"
                max="60"
                value={parameters.averageAppointmentTime}
                onChange={(e) =>
                  handleParameterChange(
                    "averageAppointmentTime",
                    e.target.value
                  )
                }
                className="w-full h-2 bg-slate-200 rounded-full appearance-none cursor-grab accent-black"
              />
            </div>

            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="text-sm font-medium text-gray-700">
                  Clinic Hours
                </label>
                <span className="text-sm font-semibold text-black bg-slate-200 px-2 py-0.5 rounded-full">
                  {parameters.clinicHours} hrs
                </span>
              </div>
              <input
                type="range"
                min="6"
                max="12"
                value={parameters.clinicHours}
                onChange={(e) =>
                  handleParameterChange("clinicHours", e.target.value)
                }
                className="w-full h-2 bg-slate-200 rounded-full appearance-none cursor-grab accent-black"
              />
            </div>
          </div>

          <button
            onClick={runSimulation}
            disabled={isRunning}
            className={`w-full mt-8 px-6 py-3.5 rounded-full font-semibold transition-all flex items-center justify-center gap-2 ${
              isRunning
                ? "bg-slate-200 text-slate-400 cursor-not-allowed"
                : "bg-black text-white hover:bg-slate-800 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 cursor-pointer"
            }`}
          >
            {isRunning ? (
              <>
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
                <span>Running Simulation...</span>
              </>
            ) : (
              <>
                <span>🚀</span>
                <span>Run Simulation</span>
              </>
            )}
          </button>
        </div>

        {/* Right section: Simulation results display */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Simulation Results</h3>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
              <div className="flex items-center gap-2 text-red-700">
                <span>{error}</span>
              </div>
            </div>
          )}

          {!simulationResults && !error && (
            <div className="text-center text-gray-500 py-8">
              <p>Run a simulation to see results</p>
            </div>
          )}

          {simulationResults && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-gray-500">
                    Average Wait Time
                  </h4>
                  <p
                    className={`text-2xl font-bold ${getWaitTimeColor(
                      simulationResults.averageWaitTime
                    )}`}
                  >
                    {simulationResults.averageWaitTime.toFixed(1)} min
                  </p>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-gray-500">
                    Doctor Utilization
                  </h4>
                  <p
                    className={`text-2xl font-bold ${getUtilizationColor(
                      simulationResults.doctorUtilization
                    )}`}
                  >
                    {simulationResults.doctorUtilization.toFixed(1)}%
                  </p>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-gray-500">
                    Patient Satisfaction
                  </h4>
                  <p className="text-2xl font-bold text-green-600">
                    {simulationResults.patientSatisfaction.toFixed(1)}%
                  </p>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-gray-500">
                    No-Show Rate
                  </h4>
                  <p className="text-2xl font-bold text-blue-600">
                    {simulationResults.noShowRate.toFixed(1)}%
                  </p>
                </div>
              </div>

              <div className="bg-blue-50 rounded-lg p-4">
                <h4 className="font-medium text-blue-800 mb-2">
                  Additional Insights
                </h4>
                <ul className="text-sm text-blue-700 space-y-1">
                  <li>
                    • Overflow patients: {simulationResults.overflowPatients}
                  </li>
                  <li>
                    • Recommended overbooking:{" "}
                    {simulationResults.recommendedOverbooking}%
                  </li>
                  <li>
                    • Current strategy:{" "}
                    {parameters.overbookingPercentage > 15
                      ? "Aggressive"
                      : parameters.overbookingPercentage > 8
                      ? "Moderate"
                      : "Conservative"}
                  </li>
                </ul>
              </div>

              <div className="bg-green-50 rounded-lg p-4">
                <h4 className="font-medium text-green-800 mb-2">
                  Recommendations
                </h4>
                <div className="text-sm text-green-700">
                  {simulationResults.averageWaitTime > 40 ? (
                    <p>
                      Consider reducing overbooking or adding more doctors to
                      improve wait times.
                    </p>
                  ) : simulationResults.doctorUtilization < 75 ? (
                    <p>
                      You can safely increase overbooking to improve efficiency.
                    </p>
                  ) : (
                    <p>
                      Current parameters are well-balanced for optimal clinic
                      performance.
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Strategy comparison table: Current vs Conservative vs Recommended */}
      {simulationResults && (
        <div className="mt-6 bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Strategy Comparison</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Strategy
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Overbooking %
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Wait Time
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Utilization
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Satisfaction
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                <tr className="bg-blue-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    Current
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {parameters.overbookingPercentage}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {simulationResults.averageWaitTime.toFixed(1)} min
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {simulationResults.doctorUtilization.toFixed(1)}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {simulationResults.patientSatisfaction.toFixed(1)}%
                  </td>
                </tr>
                <tr>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    Conservative
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    5%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    22.3 min
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    68.5%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    94.2%
                  </td>
                </tr>
                <tr>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    Recommended
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {simulationResults.recommendedOverbooking}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    28.7 min
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    82.1%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    89.8%
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

export default Simulation;
