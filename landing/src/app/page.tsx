"use client";

import { SparklesCore } from "@/components/ui/aceternity/sparkles";
import { Button } from "@/components/ui/button";
import { Github, Terminal, Zap, Shield, FileSpreadsheet } from "lucide-react";
import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen bg-black overflow-hidden selection:bg-white/30 text-white flex flex-col items-center">
      {/* Navbar Placeholder */}
      <nav className="w-full flex justify-between items-center py-6 px-8 max-w-7xl relative z-50">
        <div className="flex items-center gap-2 font-bold text-xl tracking-tight">
          <Terminal className="w-6 h-6" />
          <span>SES Emailer</span>
        </div>
        <div className="flex items-center gap-4 text-sm font-medium text-white/70">
          <Link href="#features" className="hover:text-white transition-colors">Features</Link>
          <a
            href="https://github.com/rish-kun/ses-emailer"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 hover:text-white transition-colors"
          >
            <Github className="w-4 h-4" />
            GitHub
          </a>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="h-[40rem] relative w-full flex flex-col items-center justify-center overflow-hidden rounded-md flex-grow">
        <div className="w-full absolute inset-0 min-h-screen">
          <SparklesCore
            id="tsparticlesfullpage"
            background="transparent"
            minSize={0.6}
            maxSize={1.4}
            particleDensity={100}
            className="w-full h-full"
            particleColor="#FFFFFF"
          />
        </div>
        <div className="relative z-20 flex flex-col items-center mt-[-10rem] px-4 max-w-4xl text-center">
          <div className="mb-6 px-4 py-1.5 rounded-full border border-white/10 bg-white/5 backdrop-blur-sm text-sm font-medium text-white/80 inline-flex items-center gap-2">
            <span className="flex h-2 w-2 rounded-full bg-emerald-500"></span>
            100% Free & Open Source
          </div>
          <h1 className="text-5xl md:text-7xl font-semibold tracking-tighter bg-clip-text text-transparent bg-gradient-to-b from-white to-white/60 drop-shadow-sm mb-6 pb-2 leading-tight">
            Send AWS SES Email Campaigns from your Terminal
          </h1>
          <p className="text-lg md:text-xl text-white/60 mb-10 max-w-2xl font-light">
            An elegant CLI tool for bulk email sending with Excel import, live progress, and drafts. Built for speed, security, and privacy.
          </p>
          <div className="flex flex-col sm:flex-row gap-4">
            <Button size="lg" className="rounded-full px-8 h-12 bg-white text-black hover:bg-white/90 text-sm font-semibold shadow-[0_0_40px_-10px_rgba(255,255,255,0.8)] transition-all">
              <a href="https://github.com/rish-kun/ses-emailer?tab=readme-ov-file#ses-email-sender-tui" target="_blank" rel="noopener noreferrer">
                Get Started
              </a>
            </Button>
            <Button size="lg" variant="outline" className="rounded-full px-8 h-12 border-white/20 hover:bg-white/10 hover:text-white text-white bg-transparent text-sm font-medium transition-all" asChild>
              <a href="https://github.com/rish-kun/ses-emailer" target="_blank" rel="noopener noreferrer">
                <Github className="mr-2 h-4 w-4" />
                View on GitHub
              </a>
            </Button>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <section id="features" className="w-full max-w-7xl px-8 py-24 relative z-20">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-semibold tracking-tight mb-4">Everything you need to send at scale</h2>
          <p className="text-white/60 max-w-2xl mx-auto text-lg">Powerful features wrapped in an elegant terminal user interface.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="p-8 rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm">
            <FileSpreadsheet className="w-10 h-10 text-emerald-400 mb-6" />
            <h3 className="text-xl font-medium mb-3">Excel Import</h3>
            <p className="text-white/60 leading-relaxed">Load recipient lists effortlessly from .xlsx files. Map variables directly into your email templates for personalized campaigns.</p>
          </div>

          <div className="p-8 rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm">
            <Zap className="w-10 h-10 text-blue-400 mb-6" />
            <h3 className="text-xl font-medium mb-3">Live Progress</h3>
            <p className="text-white/60 leading-relaxed">Watch your campaigns send in real-time with beautiful terminal UI progress bars and detailed delivery statistics.</p>
          </div>

          <div className="p-8 rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm">
            <Shield className="w-10 h-10 text-purple-400 mb-6" />
            <h3 className="text-xl font-medium mb-3">Secure & Private</h3>
            <p className="text-white/60 leading-relaxed">No third-party tracking. Connects directly to your AWS account. Config data is stored locally with a secure architecture.</p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="w-full border-t border-white/10 py-12 text-center text-white/40 text-sm mt-auto relative z-20">
        <p>© {new Date().getFullYear()} SES Emailer. Open source under the MIT License.</p>
        <div className="mt-4 flex justify-center gap-4">
          <a href="https://github.com/rish-kun/ses-emailer" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">GitHub Repository</a>
        </div>
      </footer>
    </main>
  );
}
