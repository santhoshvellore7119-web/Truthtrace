'use client';
import { useState } from 'react';
import Image from 'next/image';
import Link from 'next/link';

export default function Home() {
  const [claim, setClaim] = useState('');
  const [url, setUrl] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!claim.trim() && !url.trim()) {
      setError('Please enter a claim or URL to analyze');
      return;
    }

    setError(null);
    setIsAnalyzing(true);

    try {
      const response = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          claim: claim.trim() || undefined,
          url: url.trim() || undefined,
        }),
      });

      if (!response.ok) {
        throw new Error('Analysis failed');
      }

      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError('Failed to analyze claim. Please make sure the backend is running.');
      console.error(err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-zinc-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 font-sans">
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

      <main className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 py-12">
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 px-4 py-3 rounded-md mb-6">
            {error}
          </div>
        )}

        <div className="space-y-8">
          {/* Input Section */}
          <section className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6">
            <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
              Investigate a Claim
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              Enter any news claim, headline, article body, or URL to perform deep forensic verification
              across the web, news archives, and social media platforms.
            </p>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <label htmlFor="claim" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Claim or Text to Analyze
                </label>
                <textarea
                  id="claim"
                  value={claim}
                  onChange={(e) => setClaim(e.target.value)}
                  rows={4}
                  placeholder="Enter a news claim, headline, or article text to investigate..."
                  className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-blue-500 dark:focus:border-blue-400 bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 resize-none"
                />
              </div>

              <div className="space-y-2">
                <label htmlFor="url" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Or Analyze a URL
                </label>
                <input
                  id="url"
                  type="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://example.com/news-article"
                  className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-blue-500 dark:focus:border-blue-400 bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                />
              </div>

              <button
                type="submit"
                disabled={isAnalyzing}
                className="w-flex items-center justify-center px-6 py-3 bg-blue-600 dark:bg-blue-500 hover:bg-blue-700 dark:hover:bg-blue-400 text-white font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isAnalyzing ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-3 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path>
                    </svg>
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Image src="/search.svg" alt="Search" width={20} height={20} className="mr-2" />
                    Analyze Claim
                  </>
                )}
              </button>
            </form>
          </section>

          {/* Results Section */}
          {results && (
            <section className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6">
              <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
                Analysis Results
              </h2>

              {/* Verdict Badge */}
              <div className="mb-6">
                <span className={`px-3 py-1 text-xs font-medium rounded-full
                  ${getVerdictClass(results.verdict)}`}>
                  {results.verdict}
                </span>
                <span className="ml-3 text-sm text-gray-600 dark:text-gray-400">
                  Credibility Score: {results.credibility_score?.toFixed(1) ?? '0'}%
                </span>
              </div>

              {/* Timeline */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
                  Timeline & Provenance
                </h3>
                <div className="space-y-4">
                  {results.timeline?.map((event: any, index: number) => (
                    <div key={index} className="border-l-2 border-blue-300 dark:border-blue-400 pl-4">
                      <div className="flex items-start space-x-3">
                        <div className="flex-shrink-0 h-2.5 w-2.5 bg-blue-500 dark:bg-blue-400 rounded-full mt-1"></div>
                        <div>
                          <p className="text-sm text-gray-600 dark:text-gray-400">{event.timestamp}</p>
                          <p className="font-medium text-gray-900 dark:text-white">{event.event}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Patient Zero */}
              {results.patient_zero && (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
                    Patient Zero & Origin Profile
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Entity</p>
                      <p className="text-gray-900 dark:text-white">{results.patient_zero.entity}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Handle</p>
                      <p className="text-gray-900 dark:text-white">@{results.patient_zero.handle}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Platform</p>
                      <p className="text-gray-900 dark:text-white">{results.patient_zero.platform}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Account Created</p>
                      <p className="text-gray-900 dark:text-white">{results.patient_zero.account_created}</p>
                    </div>
                    <div className="md:col-span-2">
                      <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Bio</p>
                      <p className="text-gray-900 dark:text-white">{results.patient_zero.bio}</p>
                    </div>
                    <div className="md:col-span-2">
                      <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Network Affiliations</p>
                      <div className="flex flex-wrap gap-2">
                        {results.patient_zero.network_affiliations?.map((aff: string) => (
                          <span key={aff} className="bg-blue-50 dark:bg-blue-900/20 text-blue-800 dark:text-blue-200 text-xs font-medium px-2 py-1 rounded-full">
                            {aff}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Source Tweaking */}
              {results.source_tweaking && (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
                    Source Tweaking Analysis
                  </h3>
                  <div className="grid grid-cols-1 gap-6">
                    <div>
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
                        Original Statement
                      </h4>
                      <p className="bg-green-50 dark:bg-green-900/20 p-3 rounded-lg">
                        {results.source_tweaking.original_statement}
                      </p>
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
                        Claimed Statement
                      </h4>
                      <p className="bg-red-50 dark:bg-red-900/20 p-3 rounded-lg">
                        {results.source_tweaking.claimed_statement}
                      </p>
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
                        Alterations Detected
                      </h4>
                      <ul className="list-disc list-inside space-y-1 text-gray-700 dark:text-gray-300">
                        {results.source_tweaking.alterations?.map((alt: string, index: number) => (
                          <li key={index}>• {alt}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              )}

              {/* Narrative & Intention */}
              {results.narrative_intention && (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
                    Narrative & Intention Matrix
                  </h3>
                  <div className="grid grid-cols-1 gap-4">
                    <div>
                      <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Core Narrative</p>
                      <p className="text-gray-900 dark:text-white">{results.narrative_intention.core_narrative}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Emotional Hooks</p>
                      <div className="flex flex-wrap gap-2">
                        {results.narrative_intention.emotional_hooks?.map((hook: string) => (
                          <span key={hook} className="bg-purple-50 dark:bg-purple-900/20 text-purple-800 dark:text-purple-200 text-xs font-medium px-2 py-1 rounded-full">
                            {hook}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Target Demographic</p>
                      <p className="text-gray-900 dark:text-white">{results.narrative_intention.target_demographic}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Plausible Intent</p>
                      <p className="text-gray-900 dark:text-white">{results.narrative_intention.plausible_intent}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Evidence */}
              {results.evidence && (
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
                    Evidence & Sources
                  </h3>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                      <thead className="bg-gray-50 dark:bg-gray-800">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                            Source
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                            URL
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                            Timestamp
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-700">
                        {results.evidence.map((item: any, index: number) => (
                          <tr key={index} className={index % 2 === 1 ? 'bg-gray-50 dark:bg-gray-800' : ''}>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                              {item.source}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                              <a href={item.url} className="text-blue-600 dark:text-blue-400 hover:underline" target="_blank" rel="noopener noreferrer">
                                {item.url}
                              </a>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                              {item.timestamp}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Export Buttons */}
              <div className="mt-8 flex items-center space-x-3">
                <button className="flex items-center px-4 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-sm font-medium rounded-lg transition-colors">
                  <Image src="/download.svg" alt="Download" width={16} height={16} className="mr-2" />
                  Export as PDF
                </button>
                <button className="flex items-center px-4 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-sm font-medium rounded-lg transition-colors">
                  <Image src="/share.svg" alt="Share" width={16} height={16} className="mr-2" />
                  Share Report
                </button>
              </div>
            </section>
          )}
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

// Helper function to get verdict badge class
function getVerdictClass(verdict: string): string {
  const lowerVerdict = verdict.toLowerCase();
  if (lowerVerdict.includes('confirmed') || lowerVerdict.includes('mostly true')) {
    return 'bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-200';
  } else if (lowerVerdict.includes('misleading') || lowerVerdict.includes('out of context')) {
    return 'bg-yellow-100 dark:bg-yellow-900/20 text-yellow-800 dark:text-yellow-200';
  } else if (lowerVerdict.includes('fabricated')) {
    return 'bg-red-100 dark:bg-red-900/20 text-red-800 dark:text-red-200';
  } else if (lowerVerdict.includes('satire')) {
    return 'bg-blue-100 dark:bg-blue-900/20 text-blue-800 dark:text-blue-200';
  }
  return 'bg-gray-100 dark:bg-gray-900/20 text-gray-800 dark:text-gray-200';
}
