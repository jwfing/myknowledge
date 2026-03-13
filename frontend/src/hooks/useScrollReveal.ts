import { useRef, useEffect, useState, useCallback } from "react";

interface ScrollRevealOptions {
  threshold?: number;
  once?: boolean;
}

export function useScrollReveal<T extends HTMLElement>(options: ScrollRevealOptions = {}) {
  const { threshold = 0.15, once = true } = options;
  const ref = useRef<T>(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          if (once) observer.unobserve(el);
        } else if (!once) {
          setIsVisible(false);
        }
      },
      { threshold }
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, [threshold, once]);

  return { ref, isVisible };
}

/**
 * Hook for staggered children animations.
 * Returns a ref for the container and a function to get delay style for each child index.
 */
export function useStaggerReveal<T extends HTMLElement>(options: ScrollRevealOptions & { stagger?: number } = {}) {
  const { stagger = 80, ...scrollOptions } = options;
  const { ref, isVisible } = useScrollReveal<T>(scrollOptions);

  const getStaggerStyle = useCallback(
    (index: number) => ({
      transitionDelay: isVisible ? `${index * stagger}ms` : "0ms",
      opacity: isVisible ? 1 : 0,
      transform: isVisible ? "translateY(0px)" : "translateY(24px)",
      transition: "opacity 0.5s ease, transform 0.5s ease",
    }),
    [isVisible, stagger]
  );

  return { ref, isVisible, getStaggerStyle };
}
