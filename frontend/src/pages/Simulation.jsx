// src/components/Simulation.jsx
import { useState } from "react";
import { API_BASE_URL } from "../config";

function Simulation() {
  // Simulation parameter state
  const [parameters, setParameters] = useState({
    date: "",
    doctors: 1,
    slotsPerDay: 20,
    overbookingPercentage: 10,
    averageAppointmentTime: 30,
    clinicHours: 8,
  });

  // Results state and loading indicator
  const [simulationResults, setSimulationResults] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState(null);

  // Update parameter values from sliders or date input
  const handleParameterChange = (key, value) => {
    setParameters((prev) => ({
      ...prev,
      [key]: key === "date" ? value : parseInt(value),
    }));
  };

  // Run simulation via API
  const runSimulation = async () => {
    setIsRunning(true);
    setError(null);
    setSimulationResults(null);

    try {
      // Basic client-side validation
      if (!parameters.date) {
        throw new Error("Please select a simulation date.");
      }

      const response = await fetch(`${API_BASE_URL}/simulation/run`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify(parameters),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "Simulation failed");
      }

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

  // Small presenter for results blocks (keeps UI DRY)
  const ResultBlock = ({ title, data }) => {
    if (!data) return null;
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h4 className="text-lg font-semibold mb-4">{title}</h4>
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-gray-50 rounded-lg p-4">
            <h5 className="text-sm font-medium text-gray-500">Average Wait Time</h5>
            <p className={`text-2xl font-bold ${getWaitTimeColor(data.averageWaitTime ?? 0)}`}>
              {data.averageWaitTime?.toFixed(1) ?? "--"} min
            </p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <h5 className="text-sm font-medium text-gray-500">Doctor Utilization</h5>
            <p className={`text-2xl font-bold ${getUtilizationColor(data.doctorUtilization ?? 0)}`}>
              {data.doctorUtilization?.toFixed(1) ?? "--"}%
            </p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <h5 className="text-sm font-medium text-gray-500">Patient Satisfaction</h5>
            <p className="text-2xl font-bold text-green-600">
              {data.patientSatisfaction?.toFixed(1) ?? "--"}%
            </p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <h5 className="text-sm font-medium text-gray-500">No-Show Rate</h5>
            <p className="text-2xl font-bold text-blue-600">
              {data.noShowRate?.toFixed(1) ?? "--"}%
            </p>
          </div>
        </div>

        <div className="bg-blue-50 rounded-lg p-4 mt-4">
          <h5 className="font-medium text-blue-800">Additional Insights</h5>
          <ul className="text-sm text-blue-700 mt-2 space-y-1">
            <li>• Overflow patients: {data.overflowPatients ?? "--"}</li>
            <li>• Recommended overbooking: {data.recommendedOverbooking ?? "--"}%</li>
          </ul>
        </div>
      </div>
    );
  };

  return (
    <div className="max-w-7xl mx-auto">
      <div className="border-b-1 border-gray-200 py-12 mb-12">
        <h2 className="text-3xl font-bold text-gray-800">Clinic Simulation & Optimization</h2>
        <p className="text-gray-600 mt-6">
          Adjust clinic parameters and run simulations to compare historical vs model-predicted outcomes.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left section: Parameter sliders and run button */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Clinic Parameters</h3>

          <div className="mb-6">
            <label className="text-sm font-medium text-gray-700">Simulation Date</label>
            <input
              type="date"
              value={parameters.date}
              onChange={(e) => handleParameterChange("date", e.target.value)}
              className="w-full mt-2 p-2 border rounded-lg"
            />
          </div>

          <div className="space-y-6">
            {/* doctors */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="text-sm font-medium text-gray-700">Number of Doctors</label>
                <span className="text-sm font-semibold text-black bg-slate-200 px-2 py-0.5 rounded-full">{parameters.doctors}</span>
              </div>
              <input type="range" min="1" max="10" value={parameters.doctors}
                onChange={(e) => handleParameterChange("doctors", e.target.value)}
                className="w-full h-2 bg-slate-200 rounded-full appearance-none cursor-grab accent-black" />
            </div>

            {/* slotsPerDay */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="text-sm font-medium text-gray-700">Appointment Slots per Day</label>
                <span className="text-sm font-semibold text-black bg-slate-200 px-2 py-0.5 rounded-full">{parameters.slotsPerDay}</span>
              </div>
              <input type="range" min="10" max="200" value={parameters.slotsPerDay}
                onChange={(e) => handleParameterChange("slotsPerDay", e.target.value)}
                className="w-full h-2 bg-slate-200 rounded-full appearance-none cursor-grab accent-black" />
            </div>

            {/* overbooking */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="text-sm font-medium text-gray-700">Overbooking Percentage</label>
                <span className="text-sm font-semibold text-black bg-slate-200 px-2 py-0.5 rounded-full">{parameters.overbookingPercentage}%</span>
              </div>
              <input type="range" min="0" max="30" value={parameters.overbookingPercentage}
                onChange={(e) => handleParameterChange("overbookingPercentage", e.target.value)}
                className="w-full h-2 bg-slate-200 rounded-full appearance-none cursor-grab accent-black" />
            </div>

            {/* average appointment time */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="text-sm font-medium text-gray-700">Average Appointment Time</label>
                <span className="text-sm font-semibold text-black bg-slate-200 px-2 py-0.5 rounded-full">{parameters.averageAppointmentTime} min</span>
              </div>
              <input type="range" min="10" max="60" value={parameters.averageAppointmentTime}
                onChange={(e) => handleParameterChange("averageAppointmentTime", e.target.value)}
                className="w-full h-2 bg-slate-200 rounded-full appearance-none cursor-grab accent-black" />
            </div>

            {/* clinic hours */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="text-sm font-medium text-gray-700">Clinic Hours</label>
                <span className="text-sm font-semibold text-black bg-slate-200 px-2 py-0.5 rounded-full">{parameters.clinicHours} hrs</span>
              </div>
              <input type="range" min="6" max="12" value={parameters.clinicHours}
                onChange={(e) => handleParameterChange("clinicHours", e.target.value)}
                className="w-full h-2 bg-slate-200 rounded-full appearance-none cursor-grab accent-black" />
            </div>
          </div>

          <button onClick={runSimulation} disabled={isRunning}
            className={`w-full mt-8 px-6 py-3.5 rounded-full font-semibold transition-all flex items-center justify-center gap-2 ${
              isRunning ? "bg-slate-200 text-slate-400 cursor-not-allowed" : "bg-black text-white hover:bg-slate-800 shadow-lg"
            }`}>
            {isRunning ? (
              <>
                <svg className="animate-spin h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
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
          {error && <div className="mt-4 text-red-600">{error}</div>}
        </div>

        {/* Right: results */}
        <div>
          {!simulationResults && !error && (
            <div className="bg-white rounded-lg shadow p-6 text-center text-gray-500">Run a simulation to see results</div>
          )}

          {simulationResults && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <ResultBlock title="Historical (Actual) Results" data={{
                  averageWaitTime: simulationResults.actual?.averageWaitTime,
                  doctorUtilization: simulationResults.actual?.doctorUtilization,
                  patientSatisfaction: simulationResults.actual?.patientSatisfaction,
                  noShowRate: simulationResults.actual?.noShowRate,
                  overflowPatients: simulationResults.actual?.overflowPatients,
                  recommendedOverbooking: simulationResults.actual?.recommendedOverbooking
                }} />

                <ResultBlock title="Predicted (Model) Results" data={{
                  averageWaitTime: simulationResults.predicted?.averageWaitTime,
                  doctorUtilization: simulationResults.predicted?.doctorUtilization,
                  patientSatisfaction: simulationResults.predicted?.patientSatisfaction,
                  noShowRate: simulationResults.predicted?.noShowRate,
                  overflowPatients: simulationResults.predicted?.overflowPatients,
                  recommendedOverbooking: simulationResults.predicted?.recommendedOverbooking
                }} />
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <h4 className="text-lg font-semibold mb-3">Daily Summary</h4>
                <p>Date: {simulationResults.date}</p>
                <p>Source: {simulationResults.dailySource}</p>
                <p>Historical show rate: {simulationResults.daily_show_rate}%</p>
                <p>Historical no-show rate: {simulationResults.daily_no_show_rate}%</p>
                <div className="mt-4">
                  <h4 className="text-md font-semibold mb-2">
                    Predicted No-Show Statistics
                  </h4>

                  <ul className="text-sm text-gray-700 space-y-1">
                    <li>
                      Avg no-show probability:{" "}
                      {(simulationResults.predictedStats?.averageNoShowProbability * 100).toFixed(1)}%
                    </li>
                    <li>
                      Median no-show probability:{" "}
                      {(simulationResults.predictedStats?.medianNoShowProbability * 100).toFixed(1)}%
                    </li>
                    <li>
                      High risk patients: {simulationResults.predictedStats?.highRiskCount}
                    </li>
                    <li>
                      Medium risk patients: {simulationResults.predictedStats?.mediumRiskCount}
                    </li>
                    <li>
                      Low risk patients: {simulationResults.predictedStats?.lowRiskCount}
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Simulation;