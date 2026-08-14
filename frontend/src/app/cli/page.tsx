export default function CLIGuide() {
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
              <Link href="/cli" className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white font-medium font-bold">
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
              TruthTrace CLI Guide
            </h1>
            <p className="text-gray-600 dark:text-gray-400 lg:w-2/3">
              The TruthTrace Command Line Interface provides powerful disinformation analysis capabilities directly from your terminal.
              Perfect for researchers, journalists, and analysts who need to investigate claims programmatically.
            </p>
          </section>

          <section className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-8">
            <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-6">
              Installation
            </h2>
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                Prerequisites
              </h3>
              <ul className="list-disc list-inside space-y-1 pl-5 text-gray-600 dark:text-gray-400">
                <li>Python 3.8+</li>
                <li>Node.js 18+ (for full stack)</li>
                <li>API keys for search services (optional for basic functionality)</li>
              </ul>

              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2 mt-4">
                Setup
              </h3>
              <ol className="list-decimal list-inside space-y-1 pl-5 text-gray-600 dark:text-gray-400">
                <li>
                  <code className="bg-gray-100 dark:bg-gray-800/50 px-1 py-0.5 rounded">pip install -r cli/requirements.txt</code>
                </li>
                <li>
                  <code className="bg-gray-100 dark:bg-gray-800/50 px-1 py-0.5 rounded">cp cli/src/.env.example cli/src/.env</code>
                </li>
                <li>Edit <code className="bg-gray-100 dark:bg-gray-800/50 px-1 py-0.5 rounded">.env</code> to add your API keys</li>
              </ol>
            </div>
          </section>

          <section className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-8">
            <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-6">
              Usage
            </h2>
            <div className="space-y-6">
              <div className="space-y-4">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                  Basic Claim Analysis
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mb-2">
                  Analyze a text claim for misinformation and narrative intelligence:
                </p>
                <div className="bg-gray-50 dark:bg-gray-900/50 p-4 rounded-lg font-mono text-sm overflow-x-auto">
                  <code className="block">
                    python -m truthtrace.cli.src.truthtrace_cli check "The claim you want to investigate goes here"
                  </code>
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                  URL Analysis
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mb-2">
                  Analyze the content of a specific URL:
                </p>
                <div className="bg-gray-50 dark:bg-gray-900/50 p-4 rounded-lg font-mono text-sm overflow-x-auto">
                  <code className="block">
                    python -m truthtrace.cli.src.truthtrace_cli check --url "https://example.com/news-article"
                  </code>
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                  Save Results to File
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mb-2">
                  Export analysis results to a JSON file for further processing:
                </p>
                <div className="bg-gray-50 dark:bg-gray-900/50 p-4 rounded-lg font-mono text-sm overflow-x-auto">
                  <code className="block">
                    python -m truthtrace.cli.src.truthtrace_cli check "Your claim here" --output analysis.json
                  </code>
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                  Health Check
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mb-2">
                  Verify that the TruthTrace API is running:
                </p>
                <div className="bg-gray-50 dark:bg-gray-900/50 p-4 rounded-lg font-mono text-sm overflow-x-auto">
                  <code className="block">
                    python -m truthtrace.cli.src.truthtrace_cli health
                  </code>
                </div>
              </div>
            </div>
          </section>

          <section className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-8">
            <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-6">
              Example Output
            </h2>
            <div className="bg-gray-50 dark:bg-gray-900/50 p-6 rounded-lg">
              <div className="space-y-4">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                  Sample Analysis Result
                </h3>
                <pre className="p-4 rounded-lg font-mono text-sm overflow-x-auto bg-white dark:bg-gray-800"><code>{
  "verdict": "MISLEADING",
  "credibility_score": 42.5,
  "timeline": [
    {
      "timestamp": "2026-08-10T08:00:00Z",
      "event": "First appearance on Platform X"
    },
    {
      "timestamp": "2026-08-11T12:30:00Z",
      "event": "Amplified by Influencer Y"
    }
  ],
  "patient_zero": {
    "entity": "ExampleEntity",
    "handle": "@example",
    "platform": "X",
    "account_created": "2023-05-01",
    "bio": "Example bio",
    "network_affiliations": ["NetworkA", "NetworkB"]
  },
  "source_tweaking": {
    "original_statement": "The original study found no significant correlation between X and Y.",
    "claimed_statement": "The study proves that X causes Y (misrepresentation).",
    "alterations": [
      "Misinterpretation of correlation as causation",
      "Selective reporting of data"
    ]
  },
  "narrative_intention": {
    "core_narrative": "Health misinformation for profit",
    "emotional_hooks": ["Fear", "Hope"],
    "target_demographic": "Aged 35-65, health-conscious",
    "plausible_intent": "Promote unverified health products"
  },
  "evidence": [
    {
      "source": "Fact-check site",
      "url": "https://snopes.com/fact-check/example",
      "timestamp": "2026-08-12"
    }
  ]
}</code></pre>
              </div>
            </div>
          </section>

          <section className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-8">
            <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-6">
              Configuration
            </h2>
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                Environment Variables
              </h3>
              <div className="bg-gray-50 dark:bg-gray-900/50 p-4 rounded-lg">
                <div className="space-y-2">
                  <div className="flex items-start space-x-3 mb-2">
                    <Image src="/key.svg" alt="Key" width={20} height={20} className="text-warning mt-0.5" />
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">API Keys</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Required for full functionality with search APIs and social media platforms
                      </p>
                    </div>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-xs font-medium text-gray-500 dark:text-gray-400">TAVILY_API_KEY</p>
                      <p className="text-gray-900 dark:text-white font-mono">your_tavily_key_here</p>
                    </div>
                    <div>
                      <p className="text-xs font-medium text-gray-500 dark:text-gray-400">REDDIT_CLIENT_ID</p>
                      <p className="text-gray-900 dark:text-white font-mono">your_reddit_id_here</p>
                    </div>
                    <div>
                      <p className="text-xs font-medium text-gray-500 dark:text-gray-400">X_API_KEY</p>
                      <p className="text-gray-900 dark:text-white font-mono">your_x_api_key_here</p>
                    </div>
                    <div>
                      <p className="text-xs font-medium text-gray-500 dark:text-gray-400">OPENAI_API_KEY</p>
                      <p className="text-gray-900 dark:text-white font-mono">your_openai_key_here</p>
                    </div>
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