import HeroSection from "@/components/landing/HeroSection";
import FeaturesSection from "@/components/landing/FeaturesSection";
import HowItWorksSection from "@/components/landing/HowItWorksSection";
import ArchitectureSection from "@/components/landing/ArchitectureSection";
import MemoryModelSection from "@/components/landing/MemoryModelSection";
import Footer from "@/components/layout/Footer";

export default function LandingPage() {
  return (
    <>
      <HeroSection />
      <FeaturesSection />
      <HowItWorksSection />
      <ArchitectureSection />
      <MemoryModelSection />
      <Footer />
    </>
  );
}
