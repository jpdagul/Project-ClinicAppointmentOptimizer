import { useState, useEffect } from "react";
import { API_BASE_URL } from "../config";

function Dashboard({ onNavigate }) {
  const [metrics, setMetrics] = useState({
    totalPatients: 0,
    highRiskPatients: 0,
    averageWaitTime: 0,
    doctorUtilization: 0,
    patientSatisfaction: 0,
    noShowRate: 0,
    optimalOverbooking: 0,
  });

  const [weeklyData, setWeeklyData] = useState([
    { day: "Mon", appointments: 0, noShows: 0, waitTime: 0 },
    { day: "Tue", appointments: 0, noShows: 0, waitTime: 0 },
    { day: "Wed", appointments: 0, noShows: 0, waitTime: 0 },
    { day: "Thu", appointments: 0, noShows: 0, waitTime: 0 },
    { day: "Fri", appointments: 0, noShows: 0, waitTime: 0 },
    { day: "Sat", appointments: 0, noShows: 0, waitTime: 0 },
    { day: "Sun", appointments: 0, noShows: 0, waitTime: 0 },
  ]);

  const [overbookingStrategies, setOverbookingStrategies] = useState([]);
  const [insights, setInsights] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // Calculate max appointments for progress bar scaling
  const maxAppointments = weeklyData.length > 0
    ? Math.max(...weeklyData.map(day => day.appointments), 1)
    : 1;

  // Fetch dashboard data from API
  useEffect(() => {
    const fetchDashboardData = async () => {
      setIsLoading(true);
      try {
        // Fetch metrics
        const metricsResponse = await fetch(
          `${API_BASE_URL}/dashboard/metrics`,
          {
            credentials: "include",
          }
        );
        if (metricsResponse.ok) {
          const metricsData = await metricsResponse.json();
          setMetrics(metricsData);
        }

        // Fetch weekly performance
        const weeklyResponse = await fetch(
          `${API_BASE_URL}/dashboard/weekly-performance`,
          {
            credentials: "include",
          }
        );
        if (weeklyResponse.ok) {
          const weeklyData = await weeklyResponse.json();
          setWeeklyData(weeklyData);
        }

        // Fetch overbooking strategies
        const strategiesResponse = await fetch(
          `${API_BASE_URL}/dashboard/overbooking-strategies`,
          {
            credentials: "include",
          }
        );
        if (strategiesResponse.ok) {
          const strategiesData = await strategiesResponse.json();
          setOverbookingStrategies(strategiesData);
        }

        // Fetch insights
        const insightsResponse = await fetch(
          `${API_BASE_URL}/dashboard/insights`,
          {
            credentials: "include",
          }
        );
        if (insightsResponse.ok) {
          const insightsData = await insightsResponse.json();
          setInsights(insightsData);
        }
      } catch (error) {
        console.error("Dashboard data fetch error:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  // Helper function: assign color based on metric thresholds
  const getMetricColor = (value, type) => {
    if (type === "waitTime") {
      return value > 35
        ? "text-red-600"
        : value > 25
        ? "text-yellow-600"
        : "text-green-600";
    }
    if (type === "utilization") {
      return value > 90
        ? "text-red-600"
        : value > 80
        ? "text-yellow-600"
        : "text-green-600";
    }
    if (type === "satisfaction") {
      return value >= 80
        ? "text-green-600"
        : value >= 60
        ? "text-yellow-600"
        : value >= 0
        ? "text-orange-600"
        : "text-red-600";
    }
    return "text-blue-600";
  };

  // Helper function: navigate to different pages
  const go = (page) => {
    if (typeof onNavigate === "function") onNavigate(page);
  };

  return (
    <div className="max-w-7xl mx-auto">
      <div className="border-b-1 border-gray-200 py-12 mb-12">
        <h2 className="text-3xl font-bold text-gray-800">Dashboard Overview</h2>
        <p className="text-gray-600 mt-6">
          Monitor clinic performance, track patient no-show rates,and view
          optimization insights at a glance.
        </p>
      </div>

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
            <span className="text-gray-600">Loading dashboard data...</span>
          </div>
        </div>
      )}

      {/* Top metric cards: Total Patients, High Risk, Wait Time, Utilization */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                <span className="text-blue-600 font-bold">👥</span>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">
                Total Patients
              </p>
              <p className="text-2xl font-bold text-gray-900">
                {metrics.totalPatients.toLocaleString()}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
                <span className="text-red-600 font-bold">⚠️</span>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">
                High Risk Patients
              </p>
              <p className="text-2xl font-bold text-red-600">
                {metrics.highRiskPatients}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
                <span className="text-yellow-600 font-bold">⏱️</span>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Avg Wait Time</p>
              <p
                className={`text-2xl font-bold ${getMetricColor(
                  metrics.averageWaitTime,
                  "waitTime"
                )}`}
              >
                {metrics.averageWaitTime} min
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                <span className="text-green-600 font-bold">📊</span>
              </div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">
                Doctor Utilization
              </p>
              <p
                className={`text-2xl font-bold ${getMetricColor(
                  metrics.doctorUtilization,
                  "utilization"
                )}`}
              >
                {metrics.doctorUtilization}%
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Main content: Weekly performance chart and satisfaction stats */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Left section: Weekly performance by day */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Weekly Performance</h3>
          <div className="space-y-3">
            {weeklyData.map((day) => (
              <div key={day.day} className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="w-12 text-sm font-medium text-gray-600">
                    {day.day}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <div className="w-20 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ width: `${(day.appointments / maxAppointments) * 100}%` }}
                        ></div>
                      </div>
                      <span className="text-sm text-gray-600">
                        {day.appointments} appointments
                      </span>
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-red-600">
                    {day.noShows} no-shows
                  </div>
                  <div className="text-xs text-gray-500">
                    {day.waitTime}min avg wait
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right section: Patient satisfaction and no-show metrics */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">
            Patient Satisfaction & No-Shows
          </h3>
          <div className="space-y-6">
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-600">
                  Patient Satisfaction
                </span>
                <span
                  className={`text-sm font-bold ${getMetricColor(
                    metrics.patientSatisfaction,
                    "satisfaction"
                  )}`}
                >
                  {metrics.patientSatisfaction.toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3 relative">
                <div
                  className={`h-3 rounded-full ${
                    metrics.patientSatisfaction >= 80
                      ? "bg-green-600"
                      : metrics.patientSatisfaction >= 60
                      ? "bg-yellow-600"
                      : metrics.patientSatisfaction >= 0
                      ? "bg-orange-600"
                      : "bg-red-600"
                  }`}
                  style={{
                    width: `${Math.max(0, Math.min(100, metrics.patientSatisfaction))}%`,
                  }}
                ></div>
                {metrics.patientSatisfaction < 0 && (
                  <div className="absolute inset-0 flex items-center justify-start pl-2">
                    <span className="text-xs text-red-600 font-semibold">
                      {metrics.patientSatisfaction.toFixed(1)}%
                    </span>
                  </div>
                )}
              </div>
            </div>

            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-600">
                  No-Show Rate
                </span>
                <span className="text-sm font-bold text-blue-600">
                  {metrics.noShowRate.toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className="bg-blue-600 h-3 rounded-full"
                  style={{
                    width: `${Math.max(0, Math.min(100, metrics.noShowRate))}%`,
                  }}
                ></div>
              </div>
            </div>

            <div className="bg-blue-50 rounded-lg p-4">
              <h4 className="font-medium text-blue-800 mb-2">Quick Insights</h4>
              {insights && metrics.totalPatients > 0 ? (
                <ul className="text-sm text-blue-700 space-y-1">
                  {metrics.optimalOverbooking > 0 && (
                    <li>
                      • Optimal overbooking: {metrics.optimalOverbooking}%
                    </li>
                  )}
                  {insights.peakDay && (
                    <li>
                      • Peak day: {insights.peakDay.day} (
                      {insights.peakDay.appointments} appointments)
                    </li>
                  )}
                  {insights.lowestNoShows && (
                    <li>
                      • Lowest no-shows: {insights.lowestNoShows.day} (
                      {insights.lowestNoShows.rate}%)
                    </li>
                  )}
                  {insights.highestNoShows && (
                    <li>
                      • Highest no-shows: {insights.highestNoShows.day} (
                      {insights.highestNoShows.count})
                    </li>
                  )}
                </ul>
              ) : (
                <p className="text-sm text-blue-600 italic">
                  Upload patient data to see insights
                </p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Overbooking strategy comparison table */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h3 className="text-lg font-semibold mb-4">
          Overbooking Strategy Comparison
        </h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Strategy
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
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Suggested Overbooking (%)
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Recommendation
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {overbookingStrategies.map((strategy, index) => (
                <tr
                  key={index}
                  className={
                    strategy.strategy.includes("Current") ? "bg-blue-50" : ""
                  }
                >
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {strategy.strategy}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <span
                      className={getMetricColor(strategy.waitTime, "waitTime")}
                    >
                      {strategy.waitTime} min
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <span
                      className={getMetricColor(
                        strategy.utilization,
                        "utilization"
                      )}
                    >
                      {strategy.utilization}%
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <span
                      className={getMetricColor(
                        strategy.satisfaction,
                        "satisfaction"
                      )}
                    >
                      {strategy.satisfaction}%
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {strategy.suggestedOverbooking !== null ? (
                      <span className="text-blue-600">
                        {strategy.suggestedOverbooking}%
                      </span>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>

                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {strategy.strategy.includes("Optimal") ? (
                      <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                        Recommended
                      </span>
                    ) : strategy.strategy.includes("Current") ? (
                      <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                        Current
                      </span>
                    ) : (
                      <span className="text-gray-500">-</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Quick action buttons: Upload, Predictions, Simulation */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => go("upload")}
            className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors cursor-pointer"
          >
            <div className="text-center">
              <div className="text-2xl mb-2">📁</div>
              <div className="font-medium text-gray-700">Upload New Data</div>
              <div className="text-sm text-gray-500">
                Add patient information
              </div>
            </div>
          </button>
          <button
            onClick={() => go("predictions")}
            className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-green-500 hover:bg-green-50 transition-colors cursor-pointer"
          >
            <div className="text-center">
              <div className="text-2xl mb-2">🔮</div>
              <div className="font-medium text-gray-700">View Predictions</div>
              <div className="text-sm text-gray-500">Check no-show risks</div>
            </div>
          </button>
          <button
            onClick={() => go("simulation")}
            className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-purple-500 hover:bg-purple-50 transition-colors cursor-pointer"
          >
            <div className="text-center">
              <div className="text-2xl mb-2">⚙️</div>
              <div className="font-medium text-gray-700">Run Simulation</div>
              <div className="text-sm text-gray-500">Test strategies</div>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
