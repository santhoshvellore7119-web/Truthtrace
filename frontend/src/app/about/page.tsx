export default function About() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-zinc-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      <header className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm shadow-sm sticky top-0 z-20 border-b border-gray-200 dark:border-gray-700">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            <div className="flex-shrink-0 flex items-center">
              <Image
                src="/truth-logo.svg"
                alt="TruthTrace Logo"
                width={32}
                height={32}
                priority
                className="mr-3"
              />
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                TruthTrace
              </h1>
            </div>
            <nav className="hidden md:flex space-x-4">
              <Link href="/" className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white font-medium">
                Home
              </Link>
              <Link href="/about" className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white font-medium">
                About
              </Link>
              <Link href="/cli" className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white font-medium">
                CLI Guide
              </Link>
            </nav>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 py-16">
        <div className="space-y-12">
          <section className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-8">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-6">
              About TruthTrace
            </h1>
            <p className="text-gray-600 dark:text-gray-400 lg:w-2/3">
              TruthTrace is an advanced AI-powered investigative tool designed to combat misinformation and disinformation campaigns.
              Our engine combines multiple vectors of investigation to provide comprehensive analysis of news claims, social media
              narratives, and potentially manipulated content.
            </p>
          </section>

          <section className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-8">
            <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-6">
              How It Works
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div className="bg-gray-50 dark:bg-gray-900/50 p-6 rounded-lg card-hover">
                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0">
                    <Image src="/web-search.svg" alt="Web Search" width={48} height={48} className="text-primary" />
                  </div>
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                      Multi-Vector Web Investigation
                    </h3>
                    <p className="text-gray-600 dark:text-gray-400">
                      Automatically cross-references claims against fact-checking registries, news archives,
                      and global web indices to verify information accuracy.
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-gray-50 dark:bg-gray-900/50 p-6 rounded-lg card-hover">
                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0">
                    <Image src="/social.svg" alt="Social Media" width={48} height={48} className="text-accent" />
                  </div>
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                      Social Media Provenance Tracking
                    </h3>
                    <p className="text-gray-600 dark:text-gray-400">
                      Traces the earliest origin of claims across social platforms to identify "Patient Zero"
                      and map amplification patterns.
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-gray-50 dark:bg-gray-900/50 p-6 rounded-lg card-hover">
                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0">
                    <Image src="/forensics.svg" alt="Forensic Analysis" width={48} height={48} className="text-warning" />
                  </div>
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                      Forensic Anomaly Detection
                    </h3>
                    <p className="text-gray-600 dark:text-gray-400">
                      Identifies selective editing, mistranslation, or context manipulation in source materials
                      to reveal how information has been altered.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <section className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-8">
            <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-6">
              Key Features
            </h2>
            <div className="space-y-6">
              <div className="flex items-start space-x-4">
                <div className="flex-shrink-0">
                  <Image src="/check-circle.svg" alt="Check" width={24} height={24} className="text-success mt-1" />
                </div>
                <div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                    Structured Intelligence Reports
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400">
                    Comprehensive dossiers with verdicts, credibility scores, timelines, origin profiles,
                    source tweaking analysis, and narrative intent matrices.
                  </p>
                </div>
              </div>

              <div className="flex items-start space-x-4">
                <div className="flex-shrink-0">
                  <Image src="/timer.svg" alt="Timer" width={24} height={24} className="text-accent mt-1" />
                </div>
                <div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                    Real-Time Analysis
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400">
                    Get results in seconds as our AI agents work in parallel to investigate claims from multiple angles.
                  </p>
                </div>
              </div>

              <div className="flex items-start space-x-4">
                <div className="flex-shrink-0">
                  <Image src="/shield.svg" alt="Shield" width={24} height={24} className="text-error mt-1" />
                </div>
                <div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                    Defense Against Manipulation
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400">
                    Protect yourself and your organization from coordinated disinformation campaigns
                    and malicious narrative manipulation.
                  </p>
                </div>
              </div>
            </div>
          </section>

          <section className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-8">
            <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-6">
              Technology Stack
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                  Backend
                </h3>
                <div className="space-y-2 text-sm">
                  <div className="flex items-start space-x-2">
                    <Image src="/database.svg" alt="Database" width={16} height={16} className="text-gray-500 dark:text-gray-400 mt-0.5" />
                    <span>Python/FastAPI</span>
                  </div>
                  <div className="flex items-start space-x-2">
                    <Image src="/cpu.svg" alt="CPU" width={16} height={16} className="text-gray-500 dark:text-gray-400 mt-0.5" />
                    <span>Async Worker Pipeline</span>
                  </div>
                  <div className="flex items-start space-x-2">
                    <Image src="/layers.svg" alt="Layers" width={16} height={16} className="text-gray-500 dark:text-gray-400 mt-0.5" />
                    <span>Multi-Agent AI System</span>
                  </div>
                  <div className="flex items-start space-x-2">
                    <Image src="/link.svg" alt="Link" width={16} height={16} className="text-gray-500 dark:text-gray-400 mt-0.5" />
                    <span>OSINT & Web Scraping</span>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                  Frontend & CLI
                </h3>
                <div className="space-y-2 text-sm">
                  <div className="flex items-start space-x-2">
                    <Image src="/code.svg" alt="Code" width={16} height={16} className="text-gray-500 dark:text-gray-400 mt-0.5" />
                    <span>Next.js 14 (App Router)</span>
                  </div>
                  <div className="flex items-start space-x-2">
                    <Image src="/palette.svg" alt="Palette" width={16} height={16} className="text-gray-500 dark:text-gray-400 mt-0.5" />
                    <span>TypeScript & Tailwind CSS</span>
                  </div>
                  <div className="flex items-start space-x-2">
                    <Image src="/terminal.svg" alt="Terminal" width={16} height={16} className="text-gray-500 dark:text-gray-400 mt-0.5" />
                    <span>Rich CLI Interface</span>
                  </div>
                  <div className="flex items-start space-x-2">
                    <Image src="/cpu.svg" alt="CPU" width={16} height={16} className="text-gray-500 dark:text-gray-400 mt-0.5" />
                    <span>React 18 & Modern Web APIs</span>
                  </div>
                </div>
              </div>
            </div>
          </section>
        </div>
      </main>

      <footer className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm shadow-sm border-t border-gray-200 dark:border-gray-700">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between text-sm text-gray-500 dark:text-gray-400">
            <span className="flex items-center">
              <Image src="/truth-small.svg" alt="TruthTrace" width={20} height={20} className="mr-2" />
              © 2026 TruthTrace. All rights reserved.
            </span>
            <div className="flex items-center space-x-4">
              <a href="#" className="hover:text-gray-900 dark:hover:text-white">Privacy Policy</a>
              <a href="#" className="hover:text-gray-900 dark:hover:text-white">Terms of Service</a>
              <a href="#" className="hover:text-gray-900 dark:hover:text-white">Contact</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

// Mock Image component for now since we don't have actual images
import Image from 'next/image';
import Link from 'next/link';

// We'll create placeholder images or use icons from a library later
// For now, we'll use Next.js Image component with placeholder paths