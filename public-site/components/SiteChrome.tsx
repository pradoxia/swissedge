"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ThemeToggle } from "@/components/ThemeToggle";

export function ReadingProgress() {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const updateProgress = () => {
      const scrollTop = window.scrollY;
      const scrollable =
        document.documentElement.scrollHeight - window.innerHeight;
      setProgress(scrollable > 0 ? (scrollTop / scrollable) * 100 : 0);
    };

    updateProgress();
    window.addEventListener("scroll", updateProgress, { passive: true });
    window.addEventListener("resize", updateProgress);

    return () => {
      window.removeEventListener("scroll", updateProgress);
      window.removeEventListener("resize", updateProgress);
    };
  }, []);

  return (
    <div
      aria-hidden="true"
      className="reading-progress"
      style={{ width: `${progress}%` }}
    />
  );
}

export function SiteNav() {
  return (
    <header className="site-nav">
      <Link className="wordmark" href="/">
        SwissEdge
      </Link>
      <nav aria-label="Primary navigation">
        <Link href="/research">Research</Link>
        <Link href="/methodology">Methodology</Link>
        <Link href="/#source-discipline">Source Discipline</Link>
        <Link href="/#notes">Notes</Link>
      </nav>
    </header>
  );
}

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <span className="wordmark">SwissEdge</span>
      <nav aria-label="Footer navigation">
        <a href="/research">Research</a>
        <a href="/methodology">Methodology</a>
        <a href="/#disclaimer">Disclaimer</a>
      </nav>
      <p>Educational research only. Manual review required before public use.</p>
      <ThemeToggle />
    </footer>
  );
}
