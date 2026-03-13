import { Routes, Route } from "react-router-dom";
import Navbar from "@/components/layout/Navbar";
import LandingPage from "@/pages/LandingPage";
import DashboardPage from "@/pages/DashboardPage";

export default function App() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <Navbar />
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
      </Routes>
    </div>
  );
}
