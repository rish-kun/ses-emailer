import { ArrowRight, Terminal, Sparkles } from 'lucide-react';
import { motion } from 'framer-motion';

export default function Hero() {
    return (
        <div className="relative min-h-screen flex items-center justify-center overflow-hidden bg-dark">
            {/* Background Effects */}
            <div className="absolute inset-0 z-0">
                <div className="absolute inset-0 bg-[url('data:image/svg+xml,%3csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 32 32%27 width=%2732%27 height=%2732%27 fill=%27none%27 stroke=%27rgb(59 130 246 / 0.05)%27%3e%3cpath d=%27M0 .5H31.5V32%27/%3e%3c/svg%3e')] bg-[length:32px_32px]" />
                <div className="absolute top-0 right-0 -mr-40 w-96 h-96 rounded-full bg-brand-500/20 blur-[128px] pointer-events-none" />
                <div className="absolute bottom-0 left-0 -ml-40 w-[30rem] h-[30rem] rounded-full bg-indigo-500/10 blur-[128px] pointer-events-none" />
            </div>

            <div className="container relative z-10 px-6 py-24 mx-auto md:px-12 lg:px-24">
                <div className="flex flex-col items-center text-center">

                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ duration: 0.5 }}
                        className="inline-flex items-center gap-2 px-4 py-2 mb-8 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-100 text-sm font-medium"
                    >
                        <Sparkles className="w-4 h-4 text-brand-500" />
                        <span>SES Emailer is now open source</span>
                    </motion.div>

                    <motion.h1
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5, delay: 0.1 }}
                        className="mb-8 text-5xl font-bold tracking-tight md:text-7xl lg:text-8xl"
                    >
                        Command Line <br className="hidden md:block" />
                        <span className="text-gradient">Email Marketing.</span>
                    </motion.h1>

                    <motion.p
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5, delay: 0.2 }}
                        className="max-w-2xl mb-12 text-lg md:text-xl text-slate-400 font-light"
                    >
                        High-performance, secure email delivery straight from your terminal.
                        Powered by a FastAPI backend and an interactive TypeScript TUI.
                        Manage drafts, profiles, and templates with ease.
                    </motion.p>

                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.5, delay: 0.3 }}
                        className="flex flex-col sm:flex-row gap-4 w-full sm:w-auto"
                    >
                        <a
                            href="#installation"
                            className="inline-flex items-center justify-center gap-2 px-8 py-4 text-base font-semibold text-white transition-all rounded-xl bg-brand-600 hover:bg-brand-500 hover:shadow-[0_0_30px_-5px_rgba(59,130,246,0.5)] hover:-translate-y-0.5 active:translate-y-0"
                        >
                            <Terminal className="w-5 h-5" />
                            Use Now
                        </a>

                        <a
                            href="#demo"
                            className="inline-flex items-center justify-center gap-2 px-8 py-4 text-base font-medium transition-all border border-slate-700 bg-slate-800/50 hover:bg-slate-800 rounded-xl text-slate-200 hover:text-white"
                        >
                            Watch Demo
                            <ArrowRight className="w-4 h-4" />
                        </a>
                    </motion.div>

                </div>

                {/* Feature grid / Mockup Area */}
                <motion.div
                    initial={{ opacity: 0, y: 40 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.7, delay: 0.4 }}
                    className="mt-24 relative max-w-5xl mx-auto"
                >
                    <div className="absolute -inset-0.5 bg-gradient-to-r from-brand-500 to-indigo-500 rounded-2xl blur opacity-20" />
                    <div className="relative glass rounded-2xl overflow-hidden leading-none">
                        {/* Fake Mockup Header */}
                        <div className="flex items-center gap-2 px-4 py-3 border-b border-white/5 bg-slate-900/50">
                            <div className="flex gap-1.5">
                                <div className="w-3 h-3 rounded-full bg-red-500/80" />
                                <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
                                <div className="w-3 h-3 rounded-full bg-green-500/80" />
                            </div>
                            <div className="mx-auto text-xs font-medium text-slate-500 font-mono">ses-emailer --tui</div>
                        </div>
                        {/* Fake Mockup Content */}
                        <div className="p-6 md:p-8 bg-[#0d1117] font-mono text-sm sm:text-base text-slate-300">
                            <div className="flex flex-col gap-2">
                                <p><span className="text-brand-400">❯</span> Initializing SES Emailer...</p>
                                <p><span className="text-green-400">✔</span> Loaded configuration</p>
                                <p><span className="text-green-400">✔</span> Connected to FastAPI service in <span className="text-yellow-400">12ms</span></p>
                                <br />
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                                    <div className="p-4 border border-white/10 rounded-xl bg-white/5">
                                        <div className="text-slate-400 mb-1">Status</div>
                                        <div className="text-green-400 font-bold">Online</div>
                                    </div>
                                    <div className="p-4 border border-white/10 rounded-xl bg-white/5">
                                        <div className="text-slate-400 mb-1">Queue</div>
                                        <div className="text-white font-bold">0 pending</div>
                                    </div>
                                    <div className="p-4 border border-white/10 rounded-xl bg-white/5">
                                        <div className="text-slate-400 mb-1">Sent Today</div>
                                        <div className="text-brand-400 font-bold">1,245</div>
                                    </div>
                                    <div className="p-4 border border-white/10 rounded-xl bg-white/5">
                                        <div className="text-slate-400 mb-1">Profile</div>
                                        <div className="text-indigo-400 font-bold">default</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </motion.div>
            </div>
        </div>
    );
}
