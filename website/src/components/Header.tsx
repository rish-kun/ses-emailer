import { Github, Mail } from 'lucide-react';

export default function Header() {
    return (
        <header className="fixed top-0 inset-x-0 z-50 border-b border-white/5 bg-dark/80 backdrop-blur-md">
            <div className="container mx-auto px-6 h-16 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-brand-500/10 flex items-center justify-center border border-brand-500/20">
                        <Mail className="w-4 h-4 text-brand-400" />
                    </div>
                    <span className="font-bold text-lg text-white">SES Emailer</span>
                </div>

                <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-300">
                    <a href="#features" className="hover:text-white transition-colors">Features</a>
                    <a href="#how-it-works" className="hover:text-white transition-colors">How it Works</a>
                    <a href="#docs" className="hover:text-white transition-colors">Documentation</a>
                </nav>

                <div className="flex items-center gap-4">
                    <a
                        href="https://github.com/rishit-bhandari/ses-emailer"
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center gap-2 text-sm font-medium text-slate-300 hover:text-white transition-colors"
                    >
                        <Github className="w-5 h-5" />
                        <span className="hidden sm:inline">Star on GitHub</span>
                    </a>
                </div>
            </div>
        </header>
    );
}
