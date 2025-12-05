import { useState, useEffect } from "react";
import Upload from "./pages/Upload";
import Predictions from "./pages/Predictions";
import Simulation from "./pages/Simulation";
import Dashboard from "./pages/Dashboard";

function App() {
  const [currentPage, setCurrentPage] = useState("dashboard");

  // Update document title based on current page
  useEffect(() => {
    const titles = {
      dashboard: "Dashboard | Clinic Appointment Optimizer",
      upload: "Upload | Clinic Appointment Optimizer",
      predictions: "Predictions | Clinic Appointment Optimizer",
      simulation: "Simulation | Clinic Appointment Optimizer",
    };
    document.title = titles[currentPage] || "Clinic Appointment Optimizer";
  }, [currentPage]);

  // Renders the appropriate page component based on current page state
  const renderPage = () => {
    switch (currentPage) {
      case "upload":
        return <Upload />;
      case "predictions":
        return <Predictions />;
      case "simulation":
        return <Simulation />;
      case "dashboard":
      default:
        return <Dashboard onNavigate={setCurrentPage} />;
    }
  };

  return (
    <div className="min-h-screen w-full bg-gray-50">
      {/* Header section with logo, title, and project badge */}
      <header className="sticky top-0 z-50 flex flex-col bg-white border-b border-gray-200 w-full">
        <div className="flex items-center justify-between mx-9 my-6">
          <div className="flex items-center space-x-4">
            <img src="/logo.png" alt="logo" className="w-8 h-8" />
            <span className="text-gray-300"> / </span>
            <h1 className="text-l text-center font-bold text-slate-600">
              Clinic Appointment Optimizer
            </h1>
            <div className="bg-slate-300 text-black text-xs rounded-full px-2 py-1">
              Capstone Project
            </div>
          </div>
          <a
            href="https://github.com/jpdagul/Project-ClinicAppointmentOptimizer"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-xs text-gray-500 hover:text-black transition-colors"
          >
            <img src="/github.svg" alt="GitHub" className="w-5 h-5" />
            <span>Source Code</span>
          </a>
        </div>

        {/* Navigation bar with page buttons */}
        <nav>
          <div className="space-x-9 mx-9">
            <button
              onClick={() => setCurrentPage("dashboard")}
              className={`inline-flex items-center gap-1 text-xs py-4 ${
                currentPage === "dashboard"
                  ? "black border-b-2 border-black"
                  : "text-gray-400 hover:text-black"
              }`}
            >
              <span>📊</span>
              <span>Dashboard</span>
            </button>
            <button
              onClick={() => setCurrentPage("upload")}
              className={`inline-flex items-center gap-1 text-xs py-4 ${
                currentPage === "upload"
                  ? "black border-b-2 border-black"
                  : "text-gray-400 hover:text-black"
              }`}
            >
              <span>📤</span>
              <span>Upload</span>
            </button>
            <button
              onClick={() => setCurrentPage("predictions")}
              className={`inline-flex items-center gap-1 text-xs py-4 ${
                currentPage === "predictions"
                  ? "black border-b-2 border-black"
                  : "text-gray-400 hover:text-black"
              }`}
            >
              <span>🔮</span>
              <span>Predictions</span>
            </button>
            <button
              onClick={() => setCurrentPage("simulation")}
              className={`inline-flex items-center gap-1 text-xs py-4 ${
                currentPage === "simulation"
                  ? "black border-b-2 border-black"
                  : "text-gray-400 hover:text-black"
              }`}
            >
              <span>⚙️</span>
              <span>Simulation</span>
            </button>
          </div>
        </nav>
      </header>

      {/* Main content area: renders current page component */}
      <main className="w-full px-9">{renderPage()}</main>

      {/* Footer section */}
      <footer className="bg-white border-t border-gray-200 mt-12 py-8 w-full">
        <div className="flex flex-col items-center text-center space-y-4">
          <div className="flex items-center space-x-2">
            <img src="/logo.png" alt="logo" className="w-6 h-6" />
            <span className="text-sm font-bold text-slate-600">
              Clinic Appointment Optimizer
            </span>
          </div>
          <p className="text-xs text-gray-400 max-w-md">
            This is a conceptual project for educational purposes only. It does
            not use real patient data and is not intended for actual clinical
            use.
          </p>
          <div className="flex items-center space-x-2 text-xs text-gray-500">
            <span>Capstone Project</span>
            <span>·</span>
            <span>Group 1</span>
            <span>·</span>
            <span>2025</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
